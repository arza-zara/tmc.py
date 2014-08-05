import os

from peewee import (BooleanField, CharField, DateField, ForeignKeyField,
                    IntegerField, Model, SqliteDatabase)
from tmc.errors import NoCourseSelected, NoExerciseSelected

sqlite = SqliteDatabase(
    os.path.join(os.path.expanduser("~"), ".config", "tmc.db")
)
sqlite.connect()


class BaseModel(Model):

    class Meta:
        database = sqlite


class Course(BaseModel):
    tid = IntegerField(unique=True)
    name = CharField()
    is_selected = BooleanField(default=False)
    path = CharField(default="")

    def set_select(self):
        Course.update(is_selected=False).where(
            Course.is_selected == True).execute()
        self.is_selected = True
        self.save()

    @staticmethod
    def get_selected():
        selected = Course.select().where(Course.is_selected == True).first()
        if not selected:
            raise NoCourseSelected()
        return selected

    def __str__(self):
        return "Course \"{}\" (ID {})".format(self.name, self.tid)

    def __repr__(self):
        return str(self)

    def menuname(self):
        return self.name


class Exercise(BaseModel):
    tid = IntegerField(unique=True)
    name = CharField()
    course = ForeignKeyField(Course, related_name="exercises")
    is_selected = BooleanField(default=False)
    is_completed = BooleanField(default=False)
    is_downloaded = BooleanField(default=False)
    is_attempted = BooleanField(default=False)
    deadline = DateField(null=True)

    def get_course(self):
        return Course.get(Course.id == self.course)

    def path(self):
        course = Course.get(Course.id == self.course)
        return os.path.join(course.path, "/".join(self.name.split("-")))

    def set_select(self):
        Exercise.update(is_selected=False).where(
            Exercise.is_selected == True).execute()
        self.is_selected = True
        self.save()

    def update_downloaded(self):
        self.is_downloaded = os.path.isdir(self.path())
        self.save()

    @staticmethod
    def get_selected():
        is_selected = Exercise.select().where(Exercise.is_selected == True)
        first = None
        for item in is_selected:
            first = item
            break
        if not first:
            raise NoExerciseSelected()
        return first

    @staticmethod
    def byid(id):
        return Exercise.get(Exercise.tid == int(id))

    def __str__(self):
        return "Exercise \"{}\" (ID {})".format(self.name, self.tid)

    def __repr__(self):
        return str(self)

    def menuname(self):
        short, rest = "", ""
        if "-" in self.name:
            rest = self.name.split("-")[-1]
        else:
            rest = self.name
        if "." in rest:
            split = rest.split(".")
            short = split[-1]
            rest = ".".join(split[0:-1])
        realname = ""
        for c in short:
            if c.isupper():
                if len(realname) == 0:
                    realname += c
                else:
                    realname += " " + c
            else:
                realname += c
        return rest.replace("_", " - ") + " - " + realname


class Config(BaseModel):
    name = CharField(primary_key=True)
    value = CharField()

    @staticmethod
    def set(name, value):
        old = None
        try:
            old = Config.get(Config.name == name)
        except Config.DoesNotExist:
            old = None
        if old is None:
            Config.create(name=name, value=value)
        else:
            old.value = value
            old.save()

    @staticmethod
    def get_value(name):
        return Config.get(Config.name == name).value

    @staticmethod
    def has():
        try:
            Config.get(Config.name == "url")
            return True
        except Config.DoesNotExist:
            return False


class DB(object):

    def __init__(self):
        self.init()

    def init(self):
        Course.create_table(fail_silently=True)
        Exercise.create_table(fail_silently=True)
        Config.create_table(fail_silently=True)

    def reset(self):
        Course.drop_table()
        Exercise.drop_table()
        Config.drop_table()
        self.init()
