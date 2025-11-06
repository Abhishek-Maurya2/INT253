from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from devices.models import (
    DeviceCategory,
    DeviceMaterialEstimate,
    DeviceModel,
    DeviceSubmission,
)
from education.models import HazardousComponent, LearningModule
from facilities.models import Facility, FacilityAcceptedItem, FacilityService
from rewards.models import Reward


class Command(BaseCommand):
    help = "Seed demo data for the E-Waste Navigator experience."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding demo data..."))
        demo_user = self._create_demo_user()
        components = self._create_hazardous_components()
        modules = self._create_learning_modules(components)
        services = self._create_facility_services()
        facility = self._create_facility(services, components)
        self._create_facility_items(facility)
        device_models = self._create_devices(components)
        self._create_device_material_estimates(device_models)
        self._create_device_submission(demo_user, facility, device_models)
        self._create_rewards()
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def _create_demo_user(self):
        User = get_user_model()
        demo_user, created = User.objects.get_or_create(
            username="demo_user",
            defaults={
                "email": "demo@example.com",
                "first_name": "Demo",
                "last_name": "Explorer",
            },
        )
        if created:
            demo_user.set_password("demo1234")
            demo_user.save()
            self.stdout.write("  • Created demo user with username 'demo_user' and password 'demo1234'.")
        profile = demo_user.profile  # auto-created via signal
        if not profile.transactions.filter(reason="Initial sustainability bonus", source="seed_demo").exists():
            profile.adjust_credits(
                Decimal("120.00"),
                reason="Initial sustainability bonus",
                source="seed_demo",
            )
            self.stdout.write("  • Credited demo user with 120 recycling points.")
        return demo_user

    def _create_hazardous_components(self):
        records = [
            {
                "name": "Lead Solder",
                "slug": "lead-solder",
                "hazard_level": HazardousComponent.HIGH,
                "overview": "Lead-based solder can leach into soil and groundwater when electronics are landfilled.",
                "environmental_impact": "Contaminates soil ecosystems and bioaccumulates in plants and animals.",
                "human_health_impact": "Linked to nervous system damage and developmental delays, especially in children.",
                "safe_handling_guidance": "Always store lead-bearing components in sealed containers prior to recycling.",
            },
            {
                "name": "Lithium-ion Battery",
                "slug": "lithium-ion-battery",
                "hazard_level": HazardousComponent.EXTREME,
                "overview": "Lithium-ion cells pose fire risks and can release toxic gases when punctured or overheated.",
                "environmental_impact": "Battery leaks pollute waterways and soil with heavy metals and electrolytes.",
                "human_health_impact": "Exposure to vented battery chemicals can cause respiratory irritation and burns.",
                "safe_handling_guidance": "Tape terminals and store in non-conductive bins before drop-off.",
            },
            {
                "name": "Mercury Backlight",
                "slug": "mercury-backlight",
                "hazard_level": HazardousComponent.EXTREME,
                "overview": "Cold cathode fluorescent lamps in monitors contain mercury vapor that must be captured.",
                "environmental_impact": "Mercury volatilizes and travels long distances, contaminating water bodies.",
                "human_health_impact": "Mercury exposure can impair cognitive function and kidney health.",
                "safe_handling_guidance": "Never break tubes; transport whole displays in padded packaging.",
            },
        ]
        components = []
        for record in records:
            component, created = HazardousComponent.objects.update_or_create(
                slug=record["slug"], defaults=record
            )
            components.append(component)
            if created:
                self.stdout.write(f"  • Added hazardous component: {component.name}")
        return {component.slug: component for component in components}

    def _create_learning_modules(self, components):
        records = [
            {
                "title": "Safe Battery Packaging Checklist",
                "slug": "safe-battery-packaging-checklist",
                "summary": "Tape terminals, bag individually, and keep cool to avoid thermal runaway during transit.",
                "body": "Follow these best practices to prepare lithium-ion batteries for recycling drop-off, reducing fire risk for handlers.",
                "module_type": LearningModule.ACTION,
                "components": [components["lithium-ion-battery"]],
                "estimated_read_time": 4,
            },
            {
                "title": "Why Lead-Free Electronics Matter",
                "slug": "why-lead-free-electronics-matter",
                "summary": "Lead solder once dominated electronics. Learn how responsible recycling captures and stabilizes lead waste streams.",
                "body": "Lead is persistent in the environment. This module explains its impacts and how recyclers reclaim solder safely.",
                "module_type": LearningModule.AWARENESS,
                "components": [components["lead-solder"]],
                "estimated_read_time": 5,
            },
            {
                "title": "Handling Mercury Displays",
                "slug": "handling-mercury-displays",
                "summary": "Transport LCD screens with mercury backlights carefully to prevent vapor release.",
                "body": "Discover why fluorescent backlights require special containment and how to protect recycling crews.",
                "module_type": LearningModule.DEEP_DIVE,
                "components": [components["mercury-backlight"]],
                "estimated_read_time": 6,
            },
        ]
        modules = []
        for record in records:
            component_links = record.pop("components")
            module, created = LearningModule.objects.update_or_create(
                slug=record["slug"], defaults=record
            )
            module.components.set(component_links)
            modules.append(module)
            if created:
                self.stdout.write(f"  • Added learning module: {module.title}")
        return modules

    def _create_facility_services(self):
        service_data = [
            ("Battery Consolidation", "Collects, tapes, and prepares lithium cells for smelting."),
            ("Data Destruction", "Provides certified data wiping for storage devices."),
            ("CRT Processing", "Handles mercury-bearing displays and cathode ray tubes."),
        ]
        services = []
        for name, description in service_data:
            service, created = FacilityService.objects.update_or_create(
                name=name,
                defaults={"description": description},
            )
            services.append(service)
            if created:
                self.stdout.write(f"  • Added facility service: {service.name}")
        return services

    def _create_facility(self, services, components):
        facility, created = Facility.objects.update_or_create(
            slug="green-cycle-hub",
            defaults={
                "name": "Green Cycle Hub",
                "tagline": "Community-driven e-waste consolidation center",
                "description": "A certified recycling facility specializing in lithium battery handling and consumer electronics dismantling.",
                "street_address": "42 Renewal Avenue",
                "city": "Pune",
                "state_province": "Maharashtra",
                "postal_code": "411001",
                "country": "India",
                "latitude": Decimal("18.5204"),
                "longitude": Decimal("73.8567"),
                "phone_number": "+91 98765 43210",
                "email": "hello@greencyclehub.in",
                "website": "https://greencyclehub.example.com",
                "hours_of_operation": {
                    "monday": "09:30 - 18:00",
                    "tuesday": "09:30 - 18:00",
                    "wednesday": "09:30 - 18:00",
                    "thursday": "09:30 - 18:00",
                    "friday": "09:30 - 18:00",
                    "saturday": "10:00 - 14:00",
                    "sunday": "Closed",
                },
                "drop_off_instructions": "Bring devices in padded boxes, tape battery terminals, and attach submission QR codes at the gate.",
                "is_verified": True,
            },
        )
        facility.services.set(services)
        facility.focus_components.set(
            [components["lithium-ion-battery"], components["lead-solder"], components["mercury-backlight"]]
        )
        if created:
            self.stdout.write(f"  • Created facility: {facility.name}")
        return facility

    def _create_facility_items(self, facility):
        items = [
            ("Smartphones", "Remove SIM cards and perform factory reset before drop-off."),
            ("Laptops", "Include chargers separately; damaged batteries should be declared on arrival."),
            ("LCD Monitors", "Transport upright in original packaging if possible."),
        ]
        for category, notes in items:
            FacilityAcceptedItem.objects.update_or_create(
                facility=facility,
                category=category,
                defaults={"notes": notes},
            )
        self.stdout.write("  • Updated accepted item categories for facility.")

    def _create_devices(self, components):
        phone_category, _ = DeviceCategory.objects.update_or_create(
            slug="smartphones",
            defaults={
                "name": "Smartphones",
                "description": "Handheld communication devices with lithium-ion batteries.",
            },
        )
        laptop_category, _ = DeviceCategory.objects.update_or_create(
            slug="laptops",
            defaults={
                "name": "Laptops",
                "description": "Portable computers containing circuit boards, batteries, and displays.",
            },
        )
        monitor_category, _ = DeviceCategory.objects.update_or_create(
            slug="monitors",
            defaults={
                "name": "Monitors",
                "description": "Desktop displays including mercury backlights in older models.",
            },
        )

        models = []
        phone_model, created = DeviceModel.objects.update_or_create(
            slug="aurora-x1-smartphone",
            defaults={
                "category": phone_category,
                "manufacturer": "Aurora",
                "model_name": "X1",
                "release_year": 2021,
                "description": "Flagship smartphone with high-density lithium polymer battery and modular boards.",
                "estimated_points": Decimal("85.00"),
                "estimated_recovery_notes": "Contains recoverable gold-plated connectors and cobalt-rich cells.",
                "image_url": "https://images.example.com/devices/aurora-x1.jpg",
            },
        )
        phone_model.components.set(
            [components["lithium-ion-battery"], components["lead-solder"]]
        )
        if created:
            self.stdout.write(f"  • Added device model: {phone_model}")
        models.append(phone_model)

        laptop_model, created = DeviceModel.objects.update_or_create(
            slug="zenbook-pro-15",
            defaults={
                "category": laptop_category,
                "manufacturer": "ZenTech",
                "model_name": "Pro 15",
                "release_year": 2020,
                "description": "Aluminum chassis laptop with replaceable lithium battery and high-density PCBs.",
                "estimated_points": Decimal("125.00"),
                "estimated_recovery_notes": "Notable for copper heat pipes and gold in CPU pins.",
                "image_url": "https://images.example.com/devices/zentech-pro15.jpg",
            },
        )
        laptop_model.components.set(
            [components["lithium-ion-battery"], components["lead-solder"]]
        )
        if created:
            self.stdout.write(f"  • Added device model: {laptop_model}")
        models.append(laptop_model)

        monitor_model, created = DeviceModel.objects.update_or_create(
            slug="visionview-24-lcd",
            defaults={
                "category": monitor_category,
                "manufacturer": "VisionView",
                "model_name": '24" LCD',
                "release_year": 2018,
                "description": "24-inch widescreen monitor with CCFL backlighting containing mercury vapor.",
                "estimated_points": Decimal("60.00"),
                "estimated_recovery_notes": "Requires mercury capture process; contains aluminum frame.",
                "image_url": "https://images.example.com/devices/visionview-24.jpg",
            },
        )
        monitor_model.components.set(
            [components["mercury-backlight"], components["lead-solder"]]
        )
        if created:
            self.stdout.write(f"  • Added device model: {monitor_model}")
        models.append(monitor_model)

        return models

    def _create_device_material_estimates(self, device_models):
        material_map = {
            "aurora-x1-smartphone": [
                ("Gold", "0.12", "480.00"),
                ("Cobalt", "8.50", "255.00"),
            ],
            "zenbook-pro-15": [
                ("Copper", "45.00", "540.00"),
                ("Aluminum", "320.00", "320.00"),
            ],
            "visionview-24-lcd": [
                ("Aluminum", "680.00", "340.00"),
                ("Mercury", "0.10", "72.00"),
            ],
        }
        for model in device_models:
            entries = material_map.get(model.slug, [])
            for name, mass, value in entries:
                DeviceMaterialEstimate.objects.update_or_create(
                    device=model,
                    material_name=name,
                    defaults={
                        "estimated_mass_grams": Decimal(mass),
                        "estimated_value": Decimal(value),
                    },
                )
        self.stdout.write("  • Attached material recovery estimates to devices.")

    def _create_device_submission(self, user, facility, device_models):
        if not device_models:
            return
        device = device_models[0]
        submission, created = DeviceSubmission.objects.get_or_create(
            user=user,
            device_model=device,
            drop_off_facility=facility,
            defaults={
                "status": DeviceSubmission.PENDING,
                "estimated_precious_metal_mass": Decimal("0.18"),
                "estimated_credit_value": device.estimated_points,
                "message_to_facility": "Device battery is slightly swollen; please handle with caution.",
                "submitted_at": timezone.now(),
            },
        )
        if created:
            self.stdout.write(f"  • Added sample device submission for {device}.")

    def _create_rewards(self):
        rewards = [
            {
                "slug": "tree-planting-donation",
                "defaults": {
                    "name": "Tree Planting Donation",
                    "summary": "Fund the planting of two saplings in urban green belts.",
                    "description": "Redeem credits to support local NGOs planting native trees across Pune.",
                    "points_required": Decimal("150.00"),
                    "image_url": "https://images.example.com/rewards/tree-planting.jpg",
                    "partner_url": "https://sustainabilitypartners.example.com/tree-program",
                },
            },
            {
                "slug": "metro-pass-discount",
                "defaults": {
                    "name": "Metro Pass Discount",
                    "summary": "Get ₹200 off a monthly Pune Metro pass.",
                    "description": "Encourages low-carbon commutes for recycling champions.",
                    "points_required": Decimal("200.00"),
                    "image_url": "https://images.example.com/rewards/metro-pass.jpg",
                    "partner_url": "https://punemetro.example.com/rewards",
                },
            },
        ]
        for reward_data in rewards:
            reward, created = Reward.objects.update_or_create(
                slug=reward_data["slug"], defaults=reward_data["defaults"]
            )
            if created:
                self.stdout.write(f"  • Added reward: {reward.name}")
        self.stdout.write("  • Rewards catalog refreshed.")
