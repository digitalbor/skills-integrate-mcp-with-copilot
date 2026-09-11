import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
import app


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.database = tempfile.NamedTemporaryFile(delete=False)
        self.database.close()
        self.database_path = Path(self.database.name)
        app.DATABASE_PATH = self.database_path
        app.initialize_database()

    def tearDown(self):
        self.database_path.unlink(missing_ok=True)

    def test_seeded_activities_survive_reinitialization(self):
        app.signup_for_activity("Chess Club", "persistent@mergington.edu")

        app.initialize_database()

        activity = app.get_activities()["Chess Club"]
        self.assertIn("persistent@mergington.edu", activity["participants"])

    def test_duplicate_registration_is_rejected(self):
        with self.assertRaisesRegex(HTTPException, "Student is already signed up"):
            app.signup_for_activity("Chess Club", "michael@mergington.edu")

    def test_capacity_is_enforced(self):
        with app.get_connection() as connection:
            connection.execute(
                "UPDATE activities SET max_participants = 2 WHERE name = 'Chess Club'"
            )

        with self.assertRaisesRegex(HTTPException, "Activity is full"):
            app.signup_for_activity("Chess Club", "full@mergington.edu")

    def test_unregister_removes_registration(self):
        app.signup_for_activity("Chess Club", "remove@mergington.edu")

        app.unregister_from_activity("Chess Club", "remove@mergington.edu")

        self.assertNotIn(
            "remove@mergington.edu",
            app.get_activities()["Chess Club"]["participants"],
        )


if __name__ == "__main__":
    unittest.main()