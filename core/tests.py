from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from .models import Profile


class AccountTests(TestCase):
    def setUp(self):
        self.data = {"username": "reader", "email": "a@example.org", "first_name": "Анна",
                     "password1": "Planet-snow-42", "password2": "Planet-snow-42"}

    def test_registration_profile_and_redirects(self):
        response = self.client.post("/signup/", self.data)
        self.assertRedirects(response, "/")
        user = get_user_model().objects.get(username="reader")
        self.assertEqual(user.profile.user_id, user.pk)
        self.assertContains(self.client.get("/profile/"), "a@example.org")
        invalid = self.client.post("/profile/", {"first_name": "Анна", "email": "invalid"})
        self.assertFormError(invalid.context["form"], "email", "Введите правильный адрес электронной почты.")
        self.assertRedirects(self.client.post("/logout/", {"next": "/hot/?page=2"}), "/hot/?page=2")
        self.assertRedirects(self.client.get("/profile/"), "/login/?next=/profile/")
        wrong = self.client.post("/login/?next=/ask/", {"username": "reader", "password": "wrong"})
        self.assertTrue(wrong.context["form"].non_field_errors())
        self.assertContains(wrong, 'value="reader"')
        credentials = {"username": "reader", "password": self.data["password1"]}
        self.assertRedirects(self.client.post("/login/?next=/ask/", credentials), "/ask/")
        self.client.logout()
        self.assertRedirects(self.client.post("/login/?next=https://example.org/", credentials), "/")

    def test_password_validation_and_unbound_get(self):
        self.assertFalse(self.client.get("/signup/").context["form"].is_bound)
        self.data.update(password1="12345678", password2="12345678")
        response = self.client.post("/signup/", self.data)
        self.assertTrue(response.context["form"].errors["password2"])
        self.assertContains(response, 'value="a@example.org"')
        self.assertFalse(get_user_model().objects.exists())

    def test_avatar_and_profile_without_previous_profile(self):
        user = get_user_model().objects.create_user("legacy", email="a@example.org")
        self.client.force_login(user)
        fields = {"first_name": "Анна", "email": "b@example.org"}
        image = BytesIO()
        Image.new("RGB", (2, 2)).save(image, "PNG")
        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            for name, data in [("wrong.jpg", image.getvalue()), ("big.png", b"0" * (2 * 1024 * 1024 + 1))]:
                result = self.client.post("/profile/", {**fields, "avatar": SimpleUploadedFile(name, data)})
                self.assertIn("avatar", result.context["form"].errors)
            upload = SimpleUploadedFile("avatar.png", image.getvalue(), content_type="image/png")
            self.assertRedirects(self.client.post("/profile/", {**fields, "avatar": upload}), "/profile/")
            profile = Profile.objects.get(user=user)
            self.assertRegex(profile.avatar.name, r"^avatars/[a-f0-9]{32}\.png$")
            self.assertTrue(Path(profile.avatar.path).is_file())
            self.assertContains(self.client.get("/profile/"), profile.avatar.url)
            self.client.post("/profile/", fields)
            self.assertEqual(Profile.objects.get(user=user).avatar.name, profile.avatar.name)
