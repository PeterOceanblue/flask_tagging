from flask_app import app, db
from flask_app.models import TestArchive, Tag, TestTag
import csv
import os

def populate_database_from_single_csv(csv_file):
    with app.app_context():
        db.create_all()

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            unique_tags = sorted(set(row['tag'].strip() for row in reader if row['tag'].strip()))
            unique_tags.append('UNCATEGORISED')
            unique_tags = sorted(set(unique_tags))

            for tag_name in unique_tags:
                if not Tag.query.filter_by(tag=tag_name).first():
                    tag = Tag(tag=tag_name)
                    db.session.add(tag)
        
        db.session.commit()

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                test_case_id = row['Test Id']
                tag_name = row['tag'].strip() if row['tag'].strip() else 'UNCATEGORISED'
                
                test_archive = TestArchive.query.filter_by(test_case_id=test_case_id).first()
                if not test_archive:
                    test_archive = TestArchive(
                        test_case_id=row['Test Id'],
                        approval=row['Approved'],
                        version=int(row['Vers']),
                        title=row['Title'],
                        assertionText=row['Assertion'],
                        passCriteria=row['passCriteria'],
                        test_case_remark=row['remarks'],
                        testProcedure=row['testProcedure'],
                        testObject=row['testObject'],
                        optionalFeatures=row['optionalFeatures'],
                        requiredTerminalOptions=row['requiredTerminalOptions'],
                        textCondition=row['textCondition']
                    )
                    db.session.add(test_archive)

                tag = Tag.query.filter_by(tag=tag_name).first()
                
                if not TestTag.query.filter_by(test_archive_id=test_archive.id, tag_id=tag.id).first():
                    test_tag = TestTag(test_archive_id=test_archive.id, tag_id=tag.id)
                    db.session.add(test_tag)

        db.session.commit()

if __name__ == '__main__':
    csv_file_path = os.path.join(os.path.dirname(__file__), 'test_archive.csv')
    populate_database_from_single_csv(csv_file_path)
