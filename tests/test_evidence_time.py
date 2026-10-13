from evidence_time import EvidenceTime,validate_evidence_time,storage_timestamp
def test_date_precision_is_not_fabricated_into_midnight():
 x=EvidenceTime("2026-10-05","DATE","2026-10-05T10:30:00+00:00")
 assert not validate_evidence_time(x)
 assert storage_timestamp(x)=="2026-10-05T10:30:00+00:00"
 assert x.observed_value=="2026-10-05"
def test_datetime_requires_timezone():
 assert "observed_datetime_requires_timezone" in validate_evidence_time(EvidenceTime("2026-10-05T10:00:00","DATETIME","2026-10-05T11:00:00+00:00"))
