"""Source-backed lifecycle facts, not anomaly selection or causal decisions.

Every returned entity is retained. Only detail fields are projected away; raw
archives remain authoritative. No size limit or model summary edits this core.
"""
import copy
import hashlib
import json
from datetime import datetime, timezone

CORE_VERSION = 'pod-lifecycle-core.v1'
INVENTORY_VERSION = 'pod-lifecycle-inventory.v1'
# Below this many nominal Pods the full core is cheaper than explaining a roster.
ROSTER_MIN_NOMINAL = 4
NOMINAL_CRITERIA = ('phase Running with Ready=True, every app container running and ready, no termination '
                    'or restart inside the window, not deleting; or phase Succeeded')


def lightweight_handoff(material):
    protected = material.get('protected_handoff') or {}
    return (protected.get('context_policy') in {'identity.v1', 'stage.v1'}
            or (protected.get('diagnosis_handoff') or {}).get('contract_version') == 'location-handoff.v1')


def core_notice(protected):
    core = protected.get('lifecycle_core') or {}
    if not core:
        return {}
    return {'facts_in': 'protected_handoff.lifecycle_core',
            'observed_entities': len(core.get('entities') or []),
            'record_sets': len(core.get('record_sets') or {}),
            'note': '已采集的核心事实由程序独立传递，不在摘要输入中；不能据此推断未采集或没有异常。'}


def _observed(source):
    try:
        value = datetime.fromisoformat(source.get('observed_at', '').replace('Z', '+00:00'))
        return value.replace(tzinfo=value.tzinfo or timezone.utc).timestamp()
    except (ValueError, TypeError, AttributeError):
        return float('-inf')


def _object(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def lifecycle_core(value, raw_ref=None):
    data = _object(value)
    if data.get('contract_version') == CORE_VERSION:
        core = copy.deepcopy(data)
        if raw_ref:
            for source in core.get('sources', {}).values():
                if not source.get('raw_ref'):
                    source['raw_ref'] = raw_ref
        return core
    if data.get('contract_version') == 'evidence-records.v1':
        from .record_result import parse_record_result
        parsed = parse_record_result(data)
        if not parsed or not parsed[1]:
            return {}
        # Selected columns and groups are not complete Pod snapshots. Preserve
        # their explicit query/coverage rather than inventing absent Pod fields.
        packet = copy.deepcopy(data)
        source = {**packet.get('source_metadata', {}), 'raw_ref': raw_ref}
        key = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()[:24]
        query_key = hashlib.sha256(json.dumps([
            source.get('scope'), packet.get('record_unit'), packet.get('executed_query')
        ], sort_keys=True).encode()).hexdigest()[:24]
        return {'contract_version': CORE_VERSION, 'entities': [], 'sources': {key: source},
                'record_sets': {query_key: {'source': key, 'packet': packet}}}
    if data.get('contract_version') != 'pod-lifecycle.v1' or data.get('status') != 'success':
        return {}
    if not isinstance(data.get('pods'), list):
        return {}
    source = {k: copy.deepcopy(data[k]) for k in (
        'observed_at', 'scope', 'window', 'coverage', 'returned_count',
        'next_continue_token', 'remaining_item_count', 'history_complete', 'resource_version',
    ) if k in data}
    if raw_ref:
        source['raw_ref'] = raw_ref
    source_key = hashlib.sha256(
        json.dumps([{k: v for k, v in source.items() if k != 'raw_ref'}, data['pods']],
                   sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]
    entities = []
    for pod in data['pods']:
        if not isinstance(pod, dict) or not pod.get('namespace') or not pod.get('name'):
            # Invalid entities must not silently turn into a complete inventory.
            raise ValueError('Lifecycle entity is missing namespace/name')
        item = {k: copy.deepcopy(pod[k]) for k in (
            'namespace', 'name', 'uid', 'node', 'phase', 'reason', 'deletion_timestamp',
        ) if pod.get(k) is not None}
        # Keyed conditions remove repeated field names without classifying health.
        # Missing/null values remain unknown, never converted to healthy defaults.
        item['conditions'] = {condition['type']: {
            k: condition[k] for k in ('status', 'reason') if condition.get(k) is not None}
            for condition in pod.get('conditions', [])
            if condition.get('type') in ('Ready', 'ContainersReady', 'Initialized', 'PodScheduled')}
        item['containers'] = []
        for container in pod.get('containers', []):
            fact = {k: copy.deepcopy(container[k]) for k in (
                'name', 'role', 'status_observed', 'ready', 'restart_count_total',
                'termination_within_window', 'restart_count_in_window',
            ) if container.get(k) is not None}
            for field in ('state', 'last_state'):
                states = container.get(field)
                if isinstance(states, dict) and states:
                    fact[field] = {kind: {k: state[k] for k in ('reason', 'exitCode', 'signal') if k in state}
                                   for kind, state in states.items() if isinstance(state, dict)}
            item['containers'].append(fact)
        item['source'] = source_key
        entities.append(item)
    return {'contract_version': CORE_VERSION, 'entities': entities, 'sources': {source_key: source}}


def _nominal(entity):
    """Current snapshot shows nothing to investigate. Status facts only, never a health verdict."""
    if entity.get('deletion_timestamp'):
        return False
    if entity.get('phase') == 'Succeeded':
        return True
    if entity.get('phase') != 'Running':
        return False
    if (entity.get('conditions') or {}).get('Ready', {}).get('status') != 'True':
        return False
    for container in entity.get('containers') or []:
        if container.get('role', 'app') != 'app':
            continue
        if container.get('ready') is not True or set(container.get('state') or {}) != {'running'}:
            return False
        if container.get('termination_within_window') is True or (container.get('restart_count_in_window') or 0) > 0:
            return False
    return True


def inventory_view(core):
    """Model-facing view of a list-scope core: attention entities in full, nominal Pods as a roster.

    The core keeps every entity; this only decides what the model reads first. A single-Pod
    scope or a mostly-abnormal page is returned unchanged.
    """
    entities = core.get('entities') or []
    sources = core.get('sources') or {}
    if any((source.get('scope') or {}).get('pod') for source in sources.values()):
        return core
    nominal = [entity for entity in entities if _nominal(entity)]
    if len(nominal) < ROSTER_MIN_NOMINAL:
        return core
    roster = {}
    for entity in nominal:
        roster.setdefault(entity['namespace'], []).append(entity['name'])
    return {
        'contract_version': INVENTORY_VERSION,
        'sources': copy.deepcopy(sources),
        'entities': [copy.deepcopy(entity) for entity in entities if not _nominal(entity)],
        'attention_count': len(entities) - len(nominal),
        'nominal_count': len(nominal),
        'nominal_criteria': NOMINAL_CRITERIA,
        'nominal_roster': {namespace: sorted(names) for namespace, names in sorted(roster.items())},
        'note': ('Roster Pods are nominal in the current snapshot only (lastState is not full history). '
                 'Their complete records stay in raw_ref; use read_context_archive when one is needed.'),
    }


def observation_reference(observation):
    """Avoid a second copy only when the complete core is carried beside it."""
    if observation.get('semantic_success') is False:
        return observation
    core = lifecycle_core(observation.get('structured') or observation.get('result'),
                          observation.get('raw_ref'))
    if not core:
        return observation
    return {**{k: v for k, v in observation.items() if k not in ('structured', 'result')},
            'result': {'facts_in': 'protected_handoff.lifecycle_core',
                       'source_ids': list(core['sources']),
                       'entity_count': len(core['entities']),
                       'raw_ref': observation.get('raw_ref')}}


def material_without_core(material):
    """Projection used only alongside a separately preserved core contract."""
    if lightweight_handoff(material):
        # Tool records remain ordinary, summarizable evidence. Never replace
        # them with a pointer to a lifecycle core that is no longer protected.
        return material
    result = dict(material)
    if 'protected_handoff' in result:
        result['protected_handoff'] = {k: v for k, v in result['protected_handoff'].items()
                                       if k != 'lifecycle_core'}
    if 'observations' in result:
        result['observations'] = [observation_reference(o) for o in result['observations']]
    if 'recent_interactions' in result:
        result['recent_interactions'] = messages_without_core(result['recent_interactions'])
    if 'parallel_results' in result:
        result['parallel_results'] = [{**lane, 'material': material_without_core(lane.get('material') or {})}
                                      for lane in result['parallel_results']]
    return result


def messages_without_core(messages):
    for message in messages:
        data = message if isinstance(message, dict) else message.model_dump()
        if lightweight_handoff(_object(data.get('content'))):
            return messages
    result = []
    for message in messages:
        data = message if isinstance(message, dict) else message.model_dump()
        payload = _object(data.get('content'))
        role = data.get('type', data.get('role'))
        projected = None
        extras = {**(data.get('provenance') or {}), **(data.get('additional_kwargs') or {})}
        if role == 'tool' and extras.get('aiops_semantic_success') is not False and lifecycle_core(payload):
            projected = {'facts_in': 'protected_handoff.lifecycle_core'}
        elif role in ('human', 'user') and payload:
            projected = material_without_core(payload)
        if projected is None:
            result.append(message)
        else:
            content = json.dumps(projected, ensure_ascii=False, separators=(',', ':'))
            result.append({**message, 'content': content} if isinstance(message, dict)
                          else message.model_copy(update={'content': content}))
    return result


def merge_cores(*cores):
    """Latest observed snapshot per Pod name/UID; never merge two incarnations.

An omitted Pod in a partial page is not proof of deletion. Its last acquisition
remains explicitly dated. New observations replace a whole entity, not fields.
"""
    entities, sources, records = {}, {}, {}
    for core in cores:
        if not core or core.get('contract_version') != CORE_VERSION:
            continue
        sources.update(copy.deepcopy(core.get('sources') or {}))
        for query_key, record in (core.get('record_sets') or {}).items():
            old = records.get(query_key)
            if old is None or _observed(sources.get(record['source'], {})) >= _observed(sources.get(old['source'], {})):
                records[query_key] = copy.deepcopy(record)
        for item in core.get('entities') or []:
            key = (item['namespace'], item['name'])
            old = entities.get(key)
            when = _observed(sources.get(item.get('source'), {}))
            previous = _observed(sources.get((old or {}).get('source'), {}))
            if old is None or when >= previous:
                entities[key] = copy.deepcopy(item)
    if not sources:
        return {}
    # Keep coverage for the latest acquisition of each scope as well as each
    # retained entity's source; repeated per-Pod queries do not grow forever.
    latest = {}
    for key, source in sources.items():
        scope = json.dumps(source.get('scope'), sort_keys=True)
        old = latest.get(scope)
        if old is None or _observed(source) >= _observed(sources[old]):
            latest[scope] = key
    used = {item['source'] for item in entities.values()} | set(latest.values()) | {r['source'] for r in records.values()}
    result = {'contract_version': CORE_VERSION, 'entities': list(entities.values()),
              'sources': {key: source for key, source in sources.items() if key in used}}
    if records:
        result['record_sets'] = records
    return result


def core_from_material(material):
    cores = [(material.get('protected_handoff') or {}).get('lifecycle_core')]
    for observation in material.get('observations') or []:
        if observation.get('semantic_success') is False:
            continue
        cores.append(lifecycle_core(observation.get('structured') or observation.get('result'), observation.get('raw_ref')))
    cores.append(core_from_messages(material.get('recent_interactions') or []))
    for lane in material.get('parallel_results') or []:
        cores.append(core_from_material(lane.get('material') or {}))
    return merge_cores(*cores)


def core_from_messages(messages):
    cores = []
    for message in messages:
        data = message if isinstance(message, dict) else message.model_dump()
        payload = _object(data.get('content'))
        role = data.get('type', data.get('role'))
        if role == 'tool':
            extras = {**(data.get('provenance') or {}), **(data.get('additional_kwargs') or {})}
            if extras.get('aiops_semantic_success') is not False:
                cores.append(lifecycle_core(payload, extras.get('aiops_raw_ref')))
        elif role in ('human', 'user'):
            cores.append(core_from_material(payload))
    return merge_cores(*cores)
