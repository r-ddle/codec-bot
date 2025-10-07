# test_images.py
# Quick test script for image generators

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.daily_supply_gen import generate_daily_supply_card, generate_promotion_card
from utils.image_gen import generate_rank_card

print("🎮 Testing MGS Image Generators...")
print("=" * 60)

try:
    # Test 1: Rank Card
    print("\n1️⃣ Testing Rank Card...")
    rank_img = generate_rank_card(
        username="Solid Snake",
        rank_badge="🎖️",
        rank_name="Captain",
        xp=5320,
        xp_max=6000,
        gmp=125000,
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
        username="Solid Snake",
        gmp_reward=500,
        xp_reward=100,
        current_gmp=15000,
        current_xp=8500,
        current_rank="Captain",
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
        username="Big Boss",
        gmp_reward=500,
        xp_reward=100,
        current_gmp=20000,
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
        username="Revolver Ocelot",
        old_rank="Lieutenant",
        new_rank="Captain",
        current_xp=8500,
        gmp_bonus=1000,
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
        gmp=500000,
        message_count=5000,
        voice_time=1200,
        leaderboard_pos=1
    )
    unicode_img.save("test_unicode.png")
    print("   ✅ Unicode test saved as 'test_unicode.png'")

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
