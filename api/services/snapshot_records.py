"""Efficiently synchronize prepared rows within one staging snapshot."""


def sync_snapshot_records(
    *,
    model,
    snapshot,
    desired_records,
    key_fields,
    update_fields,
    batch_size,
):
    """Create new rows, update changed rows, and remove obsolete rows.

    A genuinely new snapshot naturally has no existing rows. This comparison
    matters when an incomplete staging snapshot is retried: rows whose content
    hash is already correct keep their identity and are not written again.
    """
    existing = {
        tuple(getattr(record, field) for field in key_fields): record
        for record in model.objects.filter(snapshot=snapshot)
    }
    new_records = []
    changed_records = []
    unchanged = 0
    seen = set()

    for desired in desired_records:
        key = tuple(getattr(desired, field) for field in key_fields)
        if key in seen:
            raise ValueError("Prepared snapshot rows contain a duplicate key")
        seen.add(key)

        current = existing.pop(key, None)
        if current is None:
            new_records.append(desired)
            continue
        if current.content_hash == desired.content_hash:
            unchanged += 1
            continue

        for field in update_fields:
            setattr(current, field, getattr(desired, field))
        current.content_hash = desired.content_hash
        changed_records.append(current)

    if new_records:
        model.objects.bulk_create(new_records, batch_size=batch_size)
    if changed_records:
        model.objects.bulk_update(
            changed_records,
            (*update_fields, "content_hash"),
            batch_size=batch_size,
        )
    deleted, _details = model.objects.filter(
        pk__in=[record.pk for record in existing.values()]
    ).delete()

    return {
        "created": len(new_records),
        "updated": len(changed_records),
        "unchanged": unchanged,
        "deleted": deleted,
    }
