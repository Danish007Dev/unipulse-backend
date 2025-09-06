from django.db import models
from django.utils import timezone
import datetime

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=100,default='add Course name')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    total_semesters = models.PositiveIntegerField(default=6)

    def get_semester_choices(self):
        return [str(i) for i in range(1, self.total_semesters + 1)]

    def __str__(self):
        return self.name

class Semester(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=10,default="1")

    def __str__(self):
        return f"{self.course.name} - {self.name}"

class ResearchMajor(models.Model):
    """Research specialization areas that match with research paper categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # These should match the categories from your research_fetchers.py
    MAJOR_CHOICES = [
        ('Machine Learning & AI', 'Machine Learning & AI'),
        ('Software Engineering', 'Software Engineering'),
        ('Systems & Networks', 'Systems & Networks'),
        ('Cybersecurity', 'Cybersecurity'),
        ('Human-Computer Interaction', 'Human-Computer Interaction'),
        ('Data Science & Analytics', 'Data Science & Analytics'),
        ('Emerging Technologies', 'Emerging Technologies'),
    ]
    
    category = models.CharField(max_length=50, choices=MAJOR_CHOICES, unique=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Research Major"
        verbose_name_plural = "Research Majors"
        
class Faculty(models.Model):
    name = models.CharField(max_length=100, default='Faculty')
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)
    majors = models.ManyToManyField(ResearchMajor, blank=True, related_name='faculty_members')

    def __str__(self):
        return self.email

    @property
    def role(self):
        return "faculty"
    
    @property
    def major_categories(self):
        """Get list of research categories for this faculty"""
        return [major.category for major in self.majors.all()]


class Subject(models.Model):
    name = models.CharField(max_length=100,default='Subject')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')

    def __str__(self):
        return f"{self.name} - {self.semester.course.name} Sem {self.semester.name}"


class Student(models.Model):
    name = models.CharField(max_length=100,default='Student')
    enrollment_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    # You're storing both course and department, even though Course → Department already exists.

# Suggestion: Drop department from Student model, and get it via:
# student.course.department
# This reduces denormalization and sync bugs
    def __str__(self):
        return f"{self.enrollment_number} - {self.email}"

    @property
    def role(self):
        return "student"



class Admin(models.Model):
    name = models.CharField(max_length=100, default='Admin')
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.email} - {self.department.name}"

    @property
    def role(self):
        return "admin"
    
class OTPVerification(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=15)

    def __str__(self):
        return f"{self.email} - {self.otp}"

class Post(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='posts')
   
    content = models.TextField(blank=True, null=True) # to show actual mesage (content) sent by the faculty on posts
    
    document = models.URLField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True) #when rendering posts, you’ll have subject info (if available).
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.name} - (Sem {self.semester.name} {self.content}) - {self.subject.name if self.subject else 'General'}"

    
class SavedPost(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'post')

    def __str__(self):
        return f"{self.student.email} saved {self.post.title}"
# Your models.py is now fully updated for Option A (separate models for Student, Faculty, Admin, not inheriting from Django's User). Key updates include:

# course, semester, and department fields on Student are now foreign keys.

# department on Admin is also a foreign key for consistency.

# The faculty field in Post directly uses Faculty, and SavedPost.student uses Student.

# Added a role property to each user type model to enable role checks in permissions easily.