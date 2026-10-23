from src.Models import *

def test_orgs_get_unique_ids():
    assert Org("A", "a.com").id != Org("B", "b.com").id
def test_resume_from_file_uses_filename_as_title():
    assert Resume.from_file("resumes/acme.pdf").title == "acme"