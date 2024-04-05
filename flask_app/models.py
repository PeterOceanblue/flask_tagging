from flask_app import db

class TestArchive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.String(255))
    approval = db.Column(db.String(255))
    version = db.Column(db.Integer)
    title = db.Column(db.String(255))
    assertionText = db.Column(db.String(255))
    passCriteria = db.Column(db.String(255))
    test_case_remark = db.Column(db.String(255))
    testProcedure = db.Column(db.String(255))
    testObject = db.Column(db.String(255))
    optionalFeatures = db.Column(db.String(255))
    requiredTerminalOptions = db.Column(db.String(255))
    textCondition = db.Column(db.String(255))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(255))

class TestTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_archive_id = db.Column(db.Integer, db.ForeignKey('test_archive.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))

    # Define relationships
    test_archive = db.relationship('TestArchive', backref=db.backref('test_tags', lazy=True))
    tag = db.relationship('Tag', backref=db.backref('test_tags', lazy=True))