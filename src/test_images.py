# test_images.py
# Quick test script for image generators

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.daily_supply_gen import generate_daily_supply_card, generate_promotion_card
from utils.image_gen import generate_rank_card
from utils.leaderboard_gen import generate_leaderboard
from utils.profile_card_new import generate_profile_new
from utils.profile_card_gen import generate_simple_profile_card

print("🎮 Testing MGS Image Generators...")
print("=" * 60)

try:
    # Test 1: Rank Card
    print("\n1️⃣ Testing Rank Card...")
    rank_img = generate_rank_card(
        username="Testing Long Username",
        rank_badge="🎖️",
        rank_name="Captain",
        xp=5320,
        xp_max=6000,
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        message_count=1547,
        voice_time=342,
        leaderboard_pos=7
    )
    rank_img.save("test_rank_card.png")
    print("   ✅ Rank card saved as 'test_rank_card.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 2: Daily Supply Drop (Normal)
    print("\n2️⃣ Testing Daily Supply Drop (Normal)...")
    daily_img = generate_daily_supply_card(
        username="Testing Long Username",
        xp_reward=100,
        current_xp=8500,
        current_rank="Lieutenant",
        streak_days=15,
        promoted=False
    )
    daily_img.save("test_daily_drop.png")
    print("   ✅ Daily drop card saved as 'test_daily_drop.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 3: Daily Supply Drop (With Promotion)
    print("\n3️⃣ Testing Daily Supply Drop (With Promotion)...")
    daily_promo_img = generate_daily_supply_card(
        username="Testing Long Username",
        xp_reward=100,
        current_xp=12000,
        current_rank="Major",
        streak_days=30,
        promoted=True,
        new_rank="Major",
        role_granted="Major"
    )
    daily_promo_img.save("test_daily_with_promotion.png")
    print("   ✅ Daily with promotion saved as 'test_daily_with_promotion.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 4: Promotion Card
    print("\n4️⃣ Testing Promotion Card...")
    promo_img = generate_promotion_card(
        username="Testing Long Username",
        old_rank="Lieutenant",
        new_rank="Lietutenant",
        current_xp=8500,
        role_granted="Captain"
    )
    promo_img.save("test_promotion.png")
    print("   ✅ Promotion card saved as 'test_promotion.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 5: Unicode Username Test
    print("\n5️⃣ Testing Unicode Support...")
    unicode_img = generate_rank_card(
        username="Sölïd Snäké 日本",
        rank_badge="⭐",
        rank_name="Colonel",
        xp=15000,
        xp_max=18000,
        message_count=5000,
        voice_time=1200,
        leaderboard_pos=1
    )
    unicode_img.save("test_unicode.png")
    print("   ✅ Unicode test saved as 'test_unicode.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 6: Leaderboard
    print("\n6️⃣ Testing Leaderboard...")
    leaderboard_data = [
        (1, "Testing Long Username", 15420, "FOXHOUND"),
        (2, "Big Boss", 12350, "SNAKE"),
        (3, "Solid Snake", 11890, "FOXHOUND"),
        (4, "Revolver Ocelot", 9876, "FOXHOUND"),
        (5, "Gray Fox", 8765, "FOXHOUND"),
        (6, "Meryl Silverburgh", 7654, "FOXHOUND"),
        (7, "Liquid Snake", 6543, "FOXHOUND"),
        (8, "Psycho Mantis", 5432, "FOXHOUND"),
        (9, "Sniper Wolf", 4321, "FOXHOUND"),
        (10, "Vulcan Raven", 3210, "FOXHOUND"),
    ]
    leaderboard_img = generate_leaderboard(
        leaderboard_data=leaderboard_data,
        category="EXPERIENCE POINTS",
        unit_suffix="XP",
        guild_name="OUTER HEAVEN"
    )
    leaderboard_img.save("test_leaderboard.png")
    print("   ✅ Leaderboard saved as 'test_leaderboard.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 7: Profile Card (New Design)
    print("\n7️⃣ Testing Profile Card (New Design)...")
    long_bio = """Special Operations Agent with extensive experience in covert missions and tactical operations. Expert in stealth infiltration, CQC combat, and high-risk extractions. Former member of FOXHOUND unit with classified mission history. Currently operating under the codename 'Testing Long Username' in various theaters of operation. Specialized in unconventional warfare tactics and has participated in numerous black operations across multiple continents. Maintains strict operational security protocols and has a perfect mission success rate in classified assignments."""
    profile_img = generate_profile_new(
        username="Testing Long Username",
        role_name="Captain",
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        bio_text=long_bio,
        xp=15420,
        messages=2847,
        voice_hours=156
    )
    profile_img.save("test_profile_new.png")
    print("   ✅ Profile card saved as 'test_profile_new.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    # Test 8: Profile Card (Old/Simple Design)
    print("\n8️⃣ Testing Profile Card (Old Design)...")
    simple_profile_img = generate_simple_profile_card(
        username="Testing Long Username",
        role_name="Captain",
        avatar_url="https://cdn.discordapp.com/embed/avatars/1.png",
        member_since="SEPT 2025",
        bio_text="There's nothing more for me to give you. All that's left for you to take is my life.",
        xp=15420,
        messages=2847,
        voice_hours=156
    )
    simple_profile_img.save("test_profile_simple.png")
    print("   ✅ Simple profile card saved as 'test_profile_simple.png'")

except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ All tests completed! Check the generated PNG files.")
print("\nGenerated files:")
print("  • test_rank_card.png")
print("  • test_daily_drop.png")
print("  • test_daily_with_promotion.png")
print("  • test_promotion.png")
print("  • test_unicode.png")
print("  • test_leaderboard.png")
print("  • test_profile_new.png")
print("  • test_profile_simple.png")
