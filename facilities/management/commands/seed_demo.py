from decimal import Decimal
from itertools import cycle

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

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

    DEVICE_PLACEHOLDER = "https://placehold.co/600x400?text=Device+{}"
    REWARD_PLACEHOLDER = "https://placehold.co/600x400?text=Reward+{}"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding demo data..."))
        demo_user = self._create_demo_user()
        components = self._create_hazardous_components()
        modules = self._create_learning_modules(components)
        services = self._create_facility_services()
        facilities = self._create_facilities(services, components)
        device_models = self._create_devices(components)
        self._create_device_material_estimates(device_models)
        self._create_device_submissions(demo_user, facilities, device_models)
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
            {
                "name": "Cadmium Chipset",
                "slug": "cadmium-chipset",
                "hazard_level": HazardousComponent.HIGH,
                "overview": "Cadmium-bearing chipsets can dissolve into groundwater from unprocessed e-waste.",
                "environmental_impact": "Leads to soil infertility and water contamination in nearby communities.",
                "human_health_impact": "Chronic exposure damages kidneys and skeletal integrity.",
                "safe_handling_guidance": "Seal cadmium boards in antistatic bags and label clearly for recyclers.",
            },
            {
                "name": "Brominated Flame Retardant",
                "slug": "brominated-flame-retardant",
                "hazard_level": HazardousComponent.MODERATE,
                "overview": "Used in plastic housings, BFRs release toxic dioxins when burned.",
                "environmental_impact": "Persistent organic pollutants that accumulate in wildlife.",
                "human_health_impact": "Linked to endocrine disruption and developmental toxicity.",
                "safe_handling_guidance": "Avoid shredding plastics with BFRs; send to specialized processors.",
            },
            {
                "name": "Arsenic Glass",
                "slug": "arsenic-glass",
                "hazard_level": HazardousComponent.HIGH,
                "overview": "Older CRT displays contain arsenic-doped glass requiring regulated disposal.",
                "environmental_impact": "Arsenic contaminates sediments and can enter food chains.",
                "human_health_impact": "Exposure may cause skin lesions and circulatory issues.",
                "safe_handling_guidance": "Handle with gloves and avoid breaking the vacuum tube.",
            },
            {
                "name": "Nickel Metal Hydride",
                "slug": "nickel-metal-hydride",
                "hazard_level": HazardousComponent.MODERATE,
                "overview": "NiMH packs corrode quickly, releasing alkaline electrolytes.",
                "environmental_impact": "Leached nickel reduces soil fertility and contaminates waterways.",
                "human_health_impact": "Can trigger allergic reactions and respiratory irritation.",
                "safe_handling_guidance": "Store in airtight plastic containers away from heat sources.",
            },
            {
                "name": "PCB Capacitor",
                "slug": "pcb-capacitor",
                "hazard_level": HazardousComponent.EXTREME,
                "overview": "Legacy capacitors contain polychlorinated biphenyls requiring hazardous waste treatment.",
                "environmental_impact": "Persistent pollutants that bioaccumulate in aquatic species.",
                "human_health_impact": "Associated with immune suppression and cancer risks.",
                "safe_handling_guidance": "Do not dismantle; isolate and label for specialist handlers.",
            },
            {
                "name": "PVC Cable Sheathing",
                "slug": "pvc-cable-sheathing",
                "hazard_level": HazardousComponent.MODERATE,
                "overview": "PVC insulation releases hydrochloric acid and dioxins when incinerated.",
                "environmental_impact": "Produces persistent pollutants impacting air quality.",
                "human_health_impact": "Irritates respiratory systems and can cause long-term toxicity.",
                "safe_handling_guidance": "Keep cables intact for mechanical separation and controlled recycling.",
            },
            {
                "name": "Rare Earth Magnet",
                "slug": "rare-earth-magnet",
                "hazard_level": HazardousComponent.LOW,
                "overview": "Neodymium magnets can shatter and pose ingestion hazards if not contained.",
                "environmental_impact": "Mining impacts are severe; recovery reduces the need for extraction.",
                "human_health_impact": "Strong magnets cause pinch injuries and interfere with medical devices.",
                "safe_handling_guidance": "Transport in padded boxes and keep away from electronics until processing.",
            },
        ]
        components = {}
        for record in records:
            component, created = HazardousComponent.objects.update_or_create(
                slug=record["slug"], defaults=record
            )
            components[component.slug] = component
            if created:
                self.stdout.write(f"  • Added hazardous component: {component.name}")
        return components

    def _create_learning_modules(self, components):
        records = [
            {
                "title": "Safe Battery Packaging Checklist",
                "slug": "safe-battery-packaging-checklist",
                "summary": "Tape terminals, bag individually, and keep cool to avoid thermal runaway during transit.",
                "body": "Follow these best practices to prepare lithium-ion batteries for recycling drop-off, reducing fire risk for handlers.",
                "module_type": LearningModule.ACTION,
                "component_slugs": ["lithium-ion-battery"],
                "estimated_read_time": 4,
            },
            {
                "title": "Why Lead-Free Electronics Matter",
                "slug": "why-lead-free-electronics-matter",
                "summary": "Lead solder once dominated electronics. Learn how responsible recycling captures and stabilizes lead waste streams.",
                "body": "Lead is persistent in the environment. This module explains its impacts and how recyclers reclaim solder safely.",
                "module_type": LearningModule.AWARENESS,
                "component_slugs": ["lead-solder"],
                "estimated_read_time": 5,
            },
            {
                "title": "Handling Mercury Displays",
                "slug": "handling-mercury-displays",
                "summary": "Transport LCD screens with mercury backlights carefully to prevent vapor release.",
                "body": "Discover why fluorescent backlights require special containment and how to protect recycling crews.",
                "module_type": LearningModule.DEEP_DIVE,
                "component_slugs": ["mercury-backlight"],
                "estimated_read_time": 6,
            },
            {
                "title": "Cadmium Control Workflow",
                "slug": "cadmium-control-workflow",
                "summary": "Create isolation zones for cadmium-bearing circuit boards and transport safely.",
                "body": "Cadmium requires negative-pressure handling bays. This checklist helps coordinators stay compliant.",
                "module_type": LearningModule.ACTION,
                "component_slugs": ["cadmium-chipset"],
                "estimated_read_time": 7,
            },
            {
                "title": "Understanding Flame Retardants",
                "slug": "understanding-flame-retardants",
                "summary": "Why brominated compounds complicate plastics recycling and how to mitigate risks.",
                "body": "Learn to sort plastic housings with BFR labels and route them to controlled thermal recycling streams.",
                "module_type": LearningModule.AWARENESS,
                "component_slugs": ["brominated-flame-retardant"],
                "estimated_read_time": 5,
            },
            {
                "title": "CRT Disassembly Safety",
                "slug": "crt-disassembly-safety",
                "summary": "Protect teams when depaneling arsenic-bearing CRT glass.",
                "body": "This module covers PPE, ventilation, and packaging protocols for legacy displays.",
                "module_type": LearningModule.DEEP_DIVE,
                "component_slugs": ["arsenic-glass", "lead-solder"],
                "estimated_read_time": 8,
            },
            {
                "title": "Handling NiMH Packs",
                "slug": "handling-nimh-packs",
                "summary": "Prevent alkaline leakage from nickel metal hydride batteries during transit.",
                "body": "Step-by-step tagging, taping, and boxing instructions for collection drives.",
                "module_type": LearningModule.ACTION,
                "component_slugs": ["nickel-metal-hydride"],
                "estimated_read_time": 4,
            },
            {
                "title": "Legacy Capacitor Risks",
                "slug": "legacy-capacitor-risks",
                "summary": "Map PCB capacitor hazards and archiving obligations.",
                "body": "Use this guide to inventory PCB capacitors before shipping to hazardous waste partners.",
                "module_type": LearningModule.DEEP_DIVE,
                "component_slugs": ["pcb-capacitor"],
                "estimated_read_time": 7,
            },
            {
                "title": "Cable Sorting Basics",
                "slug": "cable-sorting-basics",
                "summary": "Differentiate PVC from halogen-free sheathing to optimize recycling streams.",
                "body": "Volunteers learn how to triage cable donations using simple burn tests and markings.",
                "module_type": LearningModule.AWARENESS,
                "component_slugs": ["pvc-cable-sheathing"],
                "estimated_read_time": 3,
            },
            {
                "title": "Recovering Rare Earth Magnets",
                "slug": "recovering-rare-earth-magnets",
                "summary": "Disassemble drives to reclaim neodymium magnets for remanufacturing.",
                "body": "Demonstrates safe magnet removal techniques while preventing injury and contamination.",
                "module_type": LearningModule.ACTION,
                "component_slugs": ["rare-earth-magnet"],
                "estimated_read_time": 6,
            },
        ]
        modules = []
        for record in records:
            component_links = [components[slug] for slug in record.pop("component_slugs")]
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
            ("E-Waste Logistics", "Coordinates collection drives and bulk pickups for institutions."),
            ("Refurbishment Lab", "Restores devices for reuse and donation programs."),
            ("Component Harvesting", "Extracts reusable chips, RAM, and storage components."),
            ("Battery Second-Life", "Grades and repurposes energy storage modules."),
            ("Metals Smelting", "Ships materials to certified smelters for precious metal recovery."),
            ("Plastics Regrind", "Processes housings and cable sheathing into recycled pellets."),
            ("Device Diagnostics", "Provides advanced diagnostics for enterprise asset recovery."),
        ]
        services = {}
        for name, description in service_data:
            service, created = FacilityService.objects.update_or_create(
                name=name,
                defaults={"description": description},
            )
            services[service.name] = service
            if created:
                self.stdout.write(f"  • Added facility service: {service.name}")
        return services

    def _create_facilities(self, services, components):
        base_hours = {
            "monday": "09:30 - 18:00",
            "tuesday": "09:30 - 18:00",
            "wednesday": "09:30 - 18:00",
            "thursday": "09:30 - 18:00",
            "friday": "09:30 - 18:00",
            "saturday": "10:00 - 16:00",
            "sunday": "Closed",
        }
        facility_data = [
            {
                "slug": "green-cycle-hub",
                "name": "Green Cycle Hub",
                "tagline": "Community-driven e-waste consolidation center",
                "description": "Certified facility specializing in lithium battery handling and consumer electronics dismantling.",
                "street_address": "42 Renewal Avenue",
                "city": "Pune",
                "state_province": "Maharashtra",
                "postal_code": "411001",
                "latitude": Decimal("18.5204"),
                "longitude": Decimal("73.8567"),
                "phone_number": "+91 98765 43210",
                "email": "hello@greencyclehub.in",
                "website": "https://example.org/green-cycle",
                "services": ["Battery Consolidation", "Data Destruction", "Component Harvesting"],
                "components": ["lithium-ion-battery", "lead-solder", "mercury-backlight"],
                "accepted_items": [
                    ("Smartphones", "Remove SIM cards and perform factory reset before drop-off."),
                    ("Laptops", "Include chargers; declare damaged batteries on arrival."),
                ],
            },
            {
                "slug": "urban-reclaim-lab",
                "name": "Urban Reclaim Lab",
                "tagline": "Upcycling lab for city tech waste",
                "description": "Focuses on refurbishing laptops and harvesting reusable parts for community programs.",
                "street_address": "17 Harmony Street",
                "city": "Mumbai",
                "state_province": "Maharashtra",
                "postal_code": "400001",
                "latitude": Decimal("18.9388"),
                "longitude": Decimal("72.8354"),
                "phone_number": "+91 90909 12345",
                "email": "support@urbanreclaim.in",
                "website": "https://example.org/urban-reclaim",
                "services": ["Refurbishment Lab", "Component Harvesting", "Data Destruction"],
                "components": ["lead-solder", "nickel-metal-hydride", "pvc-cable-sheathing"],
                "accepted_items": [
                    ("Business Laptops", "Include asset tags for quick intake."),
                    ("Desktop Towers", "No loose screws or panels."),
                ],
            },
            {
                "slug": "sunrise-recycling-campus",
                "name": "Sunrise Recycling Campus",
                "tagline": "Integrated recycling campus with logistics fleet",
                "description": "Handles institutional pickups, advanced diagnostics, and responsible downstream processing.",
                "street_address": "5 Circular Road",
                "city": "Delhi",
                "state_province": "Delhi",
                "postal_code": "110001",
                "latitude": Decimal("28.6139"),
                "longitude": Decimal("77.2090"),
                "phone_number": "+91 99887 66554",
                "email": "contact@sunriserecycle.in",
                "website": "https://example.org/sunrise-campus",
                "services": ["E-Waste Logistics", "Device Diagnostics", "Battery Consolidation"],
                "components": ["cadmium-chipset", "pcb-capacitor", "lithium-ion-battery"],
                "accepted_items": [
                    ("Rack Servers", "Remove hot-swappable drives before shipment."),
                    ("UPS Units", "Disclose battery condition."),
                ],
            },
            {
                "slug": "evergreen-drop-center",
                "name": "Evergreen Drop Center",
                "tagline": "Neighborhood e-waste and plastics specialist",
                "description": "Focuses on plastics regrind and safe handling of cable insulation waste streams.",
                "street_address": "88 Lakeview Avenue",
                "city": "Bengaluru",
                "state_province": "Karnataka",
                "postal_code": "560001",
                "latitude": Decimal("12.9716"),
                "longitude": Decimal("77.5946"),
                "phone_number": "+91 91234 56789",
                "email": "team@evergreendrop.in",
                "website": "https://example.org/evergreen",
                "services": ["Plastics Regrind", "Battery Second-Life", "Data Destruction"],
                "components": ["pvc-cable-sheathing", "lead-solder", "nickel-metal-hydride"],
                "accepted_items": [
                    ("Mixed Cables", "Bundle by thickness for faster processing."),
                    ("Tablets", "Provide passcode removal confirmation."),
                ],
            },
            {
                "slug": "coastal-renew-center",
                "name": "Coastal Renew Center",
                "tagline": "Circular tech hub serving coastal districts",
                "description": "Ships processed materials to smelters and manages rare earth magnet recovery.",
                "street_address": "301 Seaview Road",
                "city": "Kochi",
                "state_province": "Kerala",
                "postal_code": "682001",
                "latitude": Decimal("9.9312"),
                "longitude": Decimal("76.2673"),
                "phone_number": "+91 93444 22110",
                "email": "hello@coastalrenew.in",
                "website": "https://example.org/coastal-renew",
                "services": ["Metals Smelting", "Battery Consolidation", "Component Harvesting"],
                "components": ["rare-earth-magnet", "lithium-ion-battery", "cadmium-chipset"],
                "accepted_items": [
                    ("Hard Drives", "Deliver in antistatic sleeves."),
                    ("Inverters", "Label weight for safe handling."),
                ],
            },
            {
                "slug": "deccan-eco-station",
                "name": "Deccan Eco Station",
                "tagline": "Educational recycling park for institutions",
                "description": "Hosts tours, learning modules, and handles arsenic and mercury bearing devices.",
                "street_address": "64 Heritage Lane",
                "city": "Hyderabad",
                "state_province": "Telangana",
                "postal_code": "500001",
                "latitude": Decimal("17.3850"),
                "longitude": Decimal("78.4867"),
                "phone_number": "+91 90000 45678",
                "email": "hello@deccaneco.in",
                "website": "https://example.org/deccan-eco",
                "services": ["CRT Processing", "Device Diagnostics", "Refurbishment Lab"],
                "components": ["mercury-backlight", "arsenic-glass", "lead-solder"],
                "accepted_items": [
                    ("Projectors", "Pack with lens covers secured."),
                    ("LCD TVs", "Retain remote controls for reuse."),
                ],
            },
            {
                "slug": "northstar-material-recovery",
                "name": "NorthStar Material Recovery",
                "tagline": "Advanced smelting and asset recovery",
                "description": "Industrial-scale facility specializing in metals smelting and diagnostics for enterprise clients.",
                "street_address": "210 Orion Park",
                "city": "Ahmedabad",
                "state_province": "Gujarat",
                "postal_code": "380001",
                "latitude": Decimal("23.0225"),
                "longitude": Decimal("72.5714"),
                "phone_number": "+91 98888 77665",
                "email": "support@northstarrecovery.in",
                "website": "https://example.org/northstar",
                "services": ["Metals Smelting", "Device Diagnostics", "Component Harvesting"],
                "components": ["cadmium-chipset", "pcb-capacitor", "rare-earth-magnet"],
                "accepted_items": [
                    ("Telecom Racks", "List circuit card part numbers."),
                    ("Industrial Controls", "Remove oil contaminants before delivery."),
                ],
            },
            {
                "slug": "eastern-loop-collective",
                "name": "Eastern Loop Collective",
                "tagline": "Community repair and reuse collective",
                "description": "Volunteers refurbish tablets and small electronics for rural education programs.",
                "street_address": "12 Learning Alley",
                "city": "Kolkata",
                "state_province": "West Bengal",
                "postal_code": "700001",
                "latitude": Decimal("22.5726"),
                "longitude": Decimal("88.3639"),
                "phone_number": "+91 92222 33445",
                "email": "team@easternloop.in",
                "website": "https://example.org/eastern-loop",
                "services": ["Refurbishment Lab", "Battery Second-Life", "Data Destruction"],
                "components": ["lithium-ion-battery", "lead-solder", "rare-earth-magnet"],
                "accepted_items": [
                    ("Tablets", "Ensure cloud locks are removed."),
                    ("Smartphones", "Battery health report appreciated."),
                ],
            },
            {
                "slug": "central-circuit-yard",
                "name": "Central Circuit Yard",
                "tagline": "Legacy electronics depollution yard",
                "description": "Processes PCB capacitors, CRTs, and provides drop-off education clinics.",
                "street_address": "91 Circuit Cross",
                "city": "Jaipur",
                "state_province": "Rajasthan",
                "postal_code": "302001",
                "latitude": Decimal("26.9124"),
                "longitude": Decimal("75.7873"),
                "phone_number": "+91 95555 44556",
                "email": "connect@circuityard.in",
                "website": "https://example.org/circuit-yard",
                "services": ["CRT Processing", "Plastics Regrind", "Battery Consolidation"],
                "components": ["pcb-capacitor", "mercury-backlight", "pvc-cable-sheathing"],
                "accepted_items": [
                    ("CRT Monitors", "Transport upright; cushioning required."),
                    ("Mixed Plastics", "Segregate ABS from PVC where possible."),
                ],
            },
            {
                "slug": "plateau-smart-collection",
                "name": "Plateau Smart Collection",
                "tagline": "Regional pickup and diagnostics hub",
                "description": "Offers enterprise-grade diagnostics and second-life battery evaluation.",
                "street_address": "55 Plateau Drive",
                "city": "Nagpur",
                "state_province": "Maharashtra",
                "postal_code": "440001",
                "latitude": Decimal("21.1458"),
                "longitude": Decimal("79.0882"),
                "phone_number": "+91 93333 11998",
                "email": "hello@plateausmart.in",
                "website": "https://example.org/plateau-smart",
                "services": ["Device Diagnostics", "Battery Second-Life", "E-Waste Logistics"],
                "components": ["nickel-metal-hydride", "lithium-ion-battery", "rare-earth-magnet"],
                "accepted_items": [
                    ("Power Tools", "Label battery chemistry before drop-off."),
                    ("Wearables", "Provide charging accessories if available."),
                ],
            },
        ]
        facilities = []
        for entry in facility_data:
            data = entry.copy()
            accepted_items = data.pop("accepted_items")
            service_names = data.pop("services")
            component_slugs = data.pop("components")
            defaults = {
                **data,
                "hours_of_operation": dict(base_hours),
                "drop_off_instructions": "Bring devices in padded boxes, tape exposed terminals, and label fragile items.",
                "is_verified": True,
            }
            facility, created = Facility.objects.update_or_create(
                slug=entry["slug"],
                defaults=defaults,
            )
            facility.services.set([services[name] for name in service_names])
            facility.focus_components.set([components[slug] for slug in component_slugs])
            for category, notes in accepted_items:
                FacilityAcceptedItem.objects.update_or_create(
                    facility=facility,
                    category=category,
                    defaults={"notes": notes},
                )
            facilities.append(facility)
            if created:
                self.stdout.write(f"  • Created facility: {facility.name}")
        self.stdout.write(f"  • Facilities available: {len(facilities)}")
        return facilities

    def _create_devices(self, components):
        category_data = [
            {"slug": "smartphones", "name": "Smartphones", "description": "Handheld communication devices with lithium cells."},
            {"slug": "laptops", "name": "Laptops", "description": "Portable computers containing high-density circuit boards."},
            {"slug": "monitors", "name": "Monitors", "description": "Desktop displays and televisions requiring depollution."},
            {"slug": "tablets", "name": "Tablets", "description": "Slate devices with integrated batteries and touchscreens."},
            {"slug": "wearables", "name": "Wearables", "description": "Smartwatches and fitness bands with small-format batteries."},
            {"slug": "audio", "name": "Audio Devices", "description": "Speakers, headphones, and soundbars."},
            {"slug": "networking", "name": "Networking", "description": "Routers, modems, and network appliances."},
            {"slug": "gaming", "name": "Gaming Consoles", "description": "Home consoles and handheld gaming systems."},
            {"slug": "appliances", "name": "Small Appliances", "description": "Compact appliances with embedded electronics."},
            {"slug": "peripherals", "name": "Peripherals", "description": "Keyboards, mice, and accessory devices."},
        ]
        categories = {}
        for entry in category_data:
            category, _ = DeviceCategory.objects.update_or_create(
                slug=entry["slug"],
                defaults=entry,
            )
            categories[category.slug] = category

        device_records = [
            {
                "slug": "aurora-x1-smartphone",
                "manufacturer": "Aurora",
                "model_name": "X1",
                "category_slug": "smartphones",
                "release_year": 2021,
                "description": "Flagship smartphone with modular boards and high-density battery.",
                "estimated_points": "85.00",
                "estimated_recovery_notes": "Recoverable gold-plated connectors and cobalt-rich cells.",
                "component_slugs": ["lithium-ion-battery", "lead-solder"],
            },
            {
                "slug": "zenbook-pro-15",
                "manufacturer": "ZenTech",
                "model_name": "Pro 15",
                "category_slug": "laptops",
                "release_year": 2020,
                "description": "Aluminum chassis laptop with replaceable lithium battery and dense PCBs.",
                "estimated_points": "125.00",
                "estimated_recovery_notes": "Copper heat pipes and gold CPU pins.",
                "component_slugs": ["lithium-ion-battery", "lead-solder"],
            },
            {
                "slug": "visionview-24-lcd",
                "manufacturer": "VisionView",
                "model_name": '24" LCD',
                "category_slug": "monitors",
                "release_year": 2018,
                "description": "24-inch widescreen monitor with CCFL backlighting containing mercury vapor.",
                "estimated_points": "60.00",
                "estimated_recovery_notes": "Needs mercury capture; aluminum frame.",
                "component_slugs": ["mercury-backlight", "lead-solder"],
            },
            {
                "slug": "orbit-tab-10",
                "manufacturer": "Orbit",
                "model_name": "Tab 10",
                "category_slug": "tablets",
                "release_year": 2022,
                "description": "Lightweight tablet with laminated display and lithium polymer pack.",
                "estimated_points": "70.00",
                "estimated_recovery_notes": "Silver traces in touch sensor and cobalt cells.",
                "component_slugs": ["lithium-ion-battery", "lead-solder"],
            },
            {
                "slug": "pulse-fit-2",
                "manufacturer": "Pulse",
                "model_name": "Fit 2",
                "category_slug": "wearables",
                "release_year": 2023,
                "description": "Fitness wearable with nickel hydride backup cell and rare earth magnets.",
                "estimated_points": "35.00",
                "estimated_recovery_notes": "Neodymium magnets and recyclable aluminum bezel.",
                "component_slugs": ["nickel-metal-hydride", "rare-earth-magnet"],
            },
            {
                "slug": "sonique-wave-soundbar",
                "manufacturer": "Sonique",
                "model_name": "Wave Soundbar",
                "category_slug": "audio",
                "release_year": 2019,
                "description": "Bluetooth soundbar with PCB capacitors and PVC cable harness.",
                "estimated_points": "55.00",
                "estimated_recovery_notes": "Copper coils and ABS housing with BFR content.",
                "component_slugs": ["pcb-capacitor", "pvc-cable-sheathing"],
            },
            {
                "slug": "netlink-ax6000",
                "manufacturer": "NetLink",
                "model_name": "AX6000",
                "category_slug": "networking",
                "release_year": 2021,
                "description": "Wi-Fi 6 router with multi-layer boards and lead-free solder.",
                "estimated_points": "40.00",
                "estimated_recovery_notes": "High copper content and reusable antennas.",
                "component_slugs": ["lead-solder", "rare-earth-magnet"],
            },
            {
                "slug": "nova-play-console",
                "manufacturer": "Nova",
                "model_name": "Play Console",
                "category_slug": "gaming",
                "release_year": 2020,
                "description": "Gaming console with high-efficiency power supply and cadmium chipsets.",
                "estimated_points": "95.00",
                "estimated_recovery_notes": "Gold contacts and rare earth magnets in drives.",
                "component_slugs": ["cadmium-chipset", "rare-earth-magnet"],
            },
            {
                "slug": "eco-blend-compact",
                "manufacturer": "EcoBlend",
                "model_name": "Compact",
                "category_slug": "appliances",
                "release_year": 2019,
                "description": "Multi-function kitchen appliance with NiMH battery backup and PCB capacitors.",
                "estimated_points": "50.00",
                "estimated_recovery_notes": "Steel chassis and copper windings in motor.",
                "component_slugs": ["nickel-metal-hydride", "pcb-capacitor"],
            },
            {
                "slug": "cloudtype-mech-pro",
                "manufacturer": "CloudType",
                "model_name": "Mech Pro",
                "category_slug": "peripherals",
                "release_year": 2024,
                "description": "Mechanical keyboard with hot-swappable switches and low-power PCB.",
                "estimated_points": "30.00",
                "estimated_recovery_notes": "Aluminum top plate and reusable switches.",
                "component_slugs": ["lead-solder", "pvc-cable-sheathing"],
            },
        ]

        models = []
        for index, record in enumerate(device_records, start=1):
            component_slugs = record["component_slugs"]
            category = categories[record["category_slug"]]
            defaults = {
                "category": category,
                "manufacturer": record["manufacturer"],
                "model_name": record["model_name"],
                "release_year": record["release_year"],
                "description": record["description"],
                "estimated_points": Decimal(record["estimated_points"]),
                "estimated_recovery_notes": record["estimated_recovery_notes"],
                "image_url": self.DEVICE_PLACEHOLDER.format(index),
            }
            device, created = DeviceModel.objects.update_or_create(
                slug=record["slug"],
                defaults=defaults,
            )
            device.components.set([components[slug] for slug in component_slugs])
            models.append(device)
            if created:
                self.stdout.write(f"  • Added device model: {device}")
        self.stdout.write(f"  • Device catalog size: {len(models)}")
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
            "orbit-tab-10": [
                ("Silver", "0.35", "210.00"),
                ("Cobalt", "6.00", "180.00"),
            ],
            "pulse-fit-2": [
                ("Neodymium", "12.00", "360.00"),
                ("Nickel", "4.50", "90.00"),
            ],
            "sonique-wave-soundbar": [
                ("Copper", "220.00", "330.00"),
                ("Steel", "950.00", "142.00"),
            ],
            "netlink-ax6000": [
                ("Copper", "180.00", "270.00"),
                ("Plastics", "420.00", "63.00"),
            ],
            "nova-play-console": [
                ("Gold", "0.25", "600.00"),
                ("Rare Earth", "35.00", "525.00"),
            ],
            "eco-blend-compact": [
                ("Copper", "390.00", "585.00"),
                ("Aluminum", "420.00", "210.00"),
            ],
            "cloudtype-mech-pro": [
                ("Aluminum", "210.00", "105.00"),
                ("Copper", "80.00", "120.00"),
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

    def _create_device_submissions(self, user, facilities, device_models):
        if not facilities or not device_models:
            return
        status_cycle = cycle(
            [
                DeviceSubmission.PENDING,
                DeviceSubmission.RECEIVED,
                DeviceSubmission.CREDITED,
                DeviceSubmission.PENDING,
                DeviceSubmission.CANCELLED,
            ]
        )
        submissions_created = 0
        for index in range(1, 11):
            device = device_models[(index - 1) % len(device_models)]
            facility = facilities[(index - 1) % len(facilities)]
            status = next(status_cycle)
            message = f"Seed submission note #{index}"
            defaults = {
                "status": status,
                "estimated_precious_metal_mass": Decimal("0.10") * index,
                "estimated_credit_value": device.estimated_points,
                "message_to_facility": message,
                "submitted_at": timezone.now(),
            }
            submission, created = DeviceSubmission.objects.update_or_create(
                user=user,
                device_model=device,
                drop_off_facility=facility,
                message_to_facility=message,
                defaults=defaults,
            )
            if created:
                submissions_created += 1
        self.stdout.write(f"  • Device submissions ensured: {submissions_created} new, 10 total records updated.")

    def _create_rewards(self):
        reward_records = [
            {
                "slug": "tree-planting-donation",
                "name": "Tree Planting Donation",
                "summary": "Fund two saplings in urban green belts.",
                "description": "Redeem credits to support local NGOs planting native trees across Pune.",
                "points_required": "150.00",
                "partner_url": "https://example.org/partners/tree",
            },
            {
                "slug": "metro-pass-discount",
                "name": "Metro Pass Discount",
                "summary": "Get ₹200 off a monthly metro pass.",
                "description": "Encourages low-carbon commutes for recycling champions.",
                "points_required": "200.00",
                "partner_url": "https://example.org/partners/metro",
            },
            {
                "slug": "solar-lantern-donation",
                "name": "Solar Lantern Donation",
                "summary": "Provide a solar lantern to a rural student.",
                "description": "Credits fund solar study lamps for off-grid communities.",
                "points_required": "180.00",
                "partner_url": "https://example.org/partners/lantern",
            },
            {
                "slug": "refill-station-card",
                "name": "Water Refill Station Card",
                "summary": "Free refills for a month at partner refill stations.",
                "description": "Stay plastic-free with participating refill hubs.",
                "points_required": "90.00",
                "partner_url": "https://example.org/partners/refill",
            },
            {
                "slug": "bike-share-pass",
                "name": "Bike Share Pass",
                "summary": "14-day bike share membership.",
                "description": "Cycle more by redeeming a complimentary pass on city bike networks.",
                "points_required": "220.00",
                "partner_url": "https://example.org/partners/bike",
            },
            {
                "slug": "compost-workshop",
                "name": "Compost Workshop Seat",
                "summary": "Join a weekend home composting workshop.",
                "description": "Hands-on training session with zero-waste mentors.",
                "points_required": "110.00",
                "partner_url": "https://example.org/partners/compost",
            },
            {
                "slug": "local-market-voucher",
                "name": "Local Market Voucher",
                "summary": "₹250 voucher for a sustainable pop-up market.",
                "description": "Redeem for package-free essentials and eco goods.",
                "points_required": "250.00",
                "partner_url": "https://example.org/partners/market",
            },
            {
                "slug": "electronics-repair-class",
                "name": "Electronics Repair Class",
                "summary": "Reserve a seat at a community repair café.",
                "description": "Learn to troubleshoot gadgets instead of landfill.",
                "points_required": "160.00",
                "partner_url": "https://example.org/partners/repair",
            },
            {
                "slug": "energy-audit-consult",
                "name": "Home Energy Audit",
                "summary": "30-minute virtual audit with an expert.",
                "description": "Identify quick wins to reduce household energy consumption.",
                "points_required": "300.00",
                "partner_url": "https://example.org/partners/energy",
            },
            {
                "slug": "urban-garden-kit",
                "name": "Urban Garden Starter Kit",
                "summary": "Redeem a balcony herb garden kit.",
                "description": "Includes planters, soil, and starter seeds for your balcony garden.",
                "points_required": "210.00",
                "partner_url": "https://example.org/partners/garden",
            },
        ]
        for index, record in enumerate(reward_records, start=1):
            defaults = {
                "name": record["name"],
                "summary": record["summary"],
                "description": record["description"],
                "points_required": Decimal(record["points_required"]),
                "partner_url": record["partner_url"],
                "image_url": self.REWARD_PLACEHOLDER.format(index),
            }
            reward, created = Reward.objects.update_or_create(
                slug=record["slug"], defaults=defaults
            )
            if created:
                self.stdout.write(f"  • Added reward: {reward.name}")
        self.stdout.write(f"  • Rewards catalog size: {len(reward_records)}")
