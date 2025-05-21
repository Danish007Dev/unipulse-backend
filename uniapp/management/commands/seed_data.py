from django.core.management.base import BaseCommand
from uniapp.models import Department, Course, Semester, Faculty, Student, Admin  # Adjust `app` to your app name
from random import randint

class Command(BaseCommand):
    help = "Seed the database with departments, courses, semesters, faculty, students, and admins"

    def handle(self, *args, **options):
        # Clear existing data
        Admin.objects.all().delete()
        Student.objects.all().delete()
        Faculty.objects.all().delete()
        Semester.objects.all().delete()
        Course.objects.all().delete()
        Department.objects.all().delete()

        print("🌱 Seeding database...")

        # 1. Create Departments
        dept_names = ["Computer Science", "Zoology", "Physics"]
        departments = []
        for name in dept_names:
            dept = Department.objects.create(name=name)
            departments.append(dept)

        # 2. Create Courses under each Department
        course_config = {
            "Computer Science": [("B.Sc CS", 6), ("M.Sc CS", 4), ("MCA", 4)],
            "Zoology": [("B.Sc Zoology", 6)],
            "Physics": [("B.Sc Physics", 6)],
        }

        course_objs = []
        for dept in departments:
            for course_name, sem_count in course_config.get(dept.name, []):
                course = Course.objects.create(name=course_name, total_semesters=sem_count, department=dept)
                course_objs.append(course)

        # 3. Create Semesters for each course
        for course in course_objs:
            for i in range(1, course.total_semesters + 1):
                Semester.objects.create(course=course, name=str(i))

        # 4. Create Faculty for each department
        all_faculty = []
        for dept in departments:
            dept_name = dept.name
            for f_index in range(1, 3):  # Create 2 faculty members
                fac_name = f"Dr. {dept_name} Faculty {f_index}"
                fac_email = f"{dept_name.lower().replace(' ', '_')}_fac{f_index}@example.com"
                faculty = Faculty.objects.create(
                    name=fac_name,
                    email=fac_email,
                    department=dept
                )
                # Assign faculty to all courses in their department
                fac_courses = Course.objects.filter(department=dept)
                faculty.courses.set(fac_courses)
                all_faculty.append(faculty)

        # 5. Create Students and Admins for each department
        for dept in departments:
            dept_name = dept.name
            dept_code = ''.join([w[0].upper() for w in dept_name.split()])  # e.g., CS

            # Get first course and its first semester
            dept_courses = Course.objects.filter(department=dept).order_by("id")
            if not dept_courses.exists():
                continue
            course = dept_courses.first()
            semester = Semester.objects.filter(course=course).order_by("id").first()

            # Create 2 students
            for i in range(1, 3):
                stu_name = f"{dept_name} Student {i}"
                stu_email = f"{dept_name.lower().replace(' ', '_')}_student{i}@example.com"
                enr_no = f"ENR-{dept_code}-{i}"
                Student.objects.create(
                    name=stu_name,
                    email=stu_email,
                    enrollment_number=enr_no,
                    course=course,
                    semester=semester,
                    department=dept
                )

            # Create 1 admin
            admin_name = f"{dept_name} Admin"
            admin_email = f"{dept_name.lower().replace(' ', '_')}_admin@example.com"
            Admin.objects.create(
                name=admin_name,
                email=admin_email,
                department=dept
            )

        print("✅ Seeding completed.")




# from django.core.management.base import BaseCommand
# from uniapp.models import Department, Course, Semester, Faculty, Student, Admin

# class Command(BaseCommand):
#     help = "Seed initial data for development or testing"

#     def handle(self, *args, **kwargs):
#         # Clear existing entries to avoid duplicates
#         Department.objects.all().delete()
#         Course.objects.all().delete()
#         Semester.objects.all().delete()
#         Faculty.objects.all().delete()
#         Student.objects.all().delete()
#         Admin.objects.all().delete()

#         # Create Departments
#         cs_dept = Department.objects.create(name="Computer Science")
#         zoo_dept = Department.objects.create(name="Zoology")
#         phy_dept = Department.objects.create(name="Physics")

#         # Create Courses
#         bsc_cs = Course.objects.create(name="BSc CS", department=cs_dept, total_semesters=6)
#         msc_cs = Course.objects.create(name="MSc CS", department=cs_dept, total_semesters=4)
#         mca_cs = Course.objects.create(name="MCA CS", department=cs_dept, total_semesters=4)
#         bsc_zoo = Course.objects.create(name="BSc Zoology", department=zoo_dept, total_semesters=6)
#         bsc_phy = Course.objects.create(name="BSc Physics", department=phy_dept, total_semesters=6)

        # # Create Semesters
        # for course in [bsc_cs, msc_cs, mca_cs, bsc_zoo, bsc_phy]:
        #     for i in range(1, course.total_semesters + 1):
        #         Semester.objects.create(course=course, name=str(i))

#         # Get semester instances for student creation
#         mca_cs_sem1 = Semester.objects.get(course=mca_cs, name="1")
#         bsc_zoo_sem1 = Semester.objects.get(course=bsc_zoo, name="1")

#         # Create Faculty
#         fac = Faculty.objects.create(email="danstd3@gmail.com", department=cs_dept)
#         fac.courses.set([bsc_cs, msc_cs, mca_cs])

#         # Create Students
#         Student.objects.create(
#             enrollment_number="GP6638",
#             email="danstd3@gmail.com",
#             course=mca_cs,
#             semester=mca_cs_sem1,
#             department=cs_dept
#         )

#         Student.objects.create(
#             enrollment_number="GP6637",
#             email="danmade221@gmail.com",
#             course=bsc_zoo,
#             semester=bsc_zoo_sem1,
#             department=zoo_dept
#         )

#         # Create Admin
#         Admin.objects.create(
#             email="danstd3@gmail.com",
#             department=cs_dept
#         )

#         self.stdout.write(self.style.SUCCESS("✅ Seed data populated successfully."))




