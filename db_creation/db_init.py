from flask_app import app ,db
from flask_app.models import TestArchive, Tag, TestTag
import csv

# Define a function to populate the database from CSV files
def populate_database():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Populate TestArchive table
        with open('test_archive.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                test_archive = TestArchive(
                    test_case_id=row['test_case_id'],
                    approval=row['Approval'],
                    version=int(row['version']),
                    title=row['title'],
                    assertionText=row['assertionText'],
                    passCriteria=row['passCriteria'],
                    test_case_remark=row['remarks'],
                    testProcedure=row['testProcedure'],
                    testObject=row['testObject'],
                    optionalFeatures=row['optionalFeatures'],
                    requiredTerminalOptions=row['requiredTerminalOptions'],
                    textCondition=row['textCondition']
                )
                db.session.add(test_archive)

        # Populate Tag table
        with open('tags.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tag = Tag(tag=row['tag'])
                db.session.add(tag)

        # Populate TestTag table
        with open('test_tag.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                test_tag = TestTag(
                    test_archive_id=int(row['test_archive_id']),
                    tag_id=int(row['tag_id'])
                )
                db.session.add(test_tag)

        db.session.commit()

# Call the populate_database function if executed directly
if __name__ == '__main__':
    populate_database()
