"""
Constants for Kira - r.ddle's Exile Server Bot
"""
from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════════
# SERVER IDENTITY
# ═══════════════════════════════════════════════════════════════════
SERVER_NAME = "Exile"
SERVER_OWNER = "r.ddle"
SERVER_FOOTER = "© 2025 EXILE - r.ddle's Hangout"

# ═══════════════════════════════════════════════════════════════════
# COMMAND NAMES (Customize command names here)
# ═══════════════════════════════════════════════════════════════════
COMMAND_NAMES = {
    # Progression commands
    "status": "status",          # Check your rank and XP
    "rank": "rank",              # View rank card
    "leaderboard": "leaderboard", # View leaderboards
    "daily": "daily",            # Daily supply drop

    # Info commands

    # Profile commands
    "profile": "profile",        # View profile card
    "setbio": "setbio",         # Set profile bio

    # Admin commands (keep these hidden from help)
    "sync": "sync",
    "backup": "backup",
    "event": "event",
}

# MGS-themed messages
MGS_QUOTES: List[str] = [
    "Kept you waiting, huh?",
    "Snake? Snake?! SNAAAAKE!",
    "I'm no hero. Never was, never will be.",
    "Metal Gear?!",
    "War has changed...",
    "Nanomachines, son!",
    "This is good... isn't it?",
    "A weapon to surpass Metal Gear!",
    "Brother!",
    "You're pretty good.",
    "The future is not some place we are going, but one we are creating."
]



# XP-BASED RANK PROGRESSION SYSTEM (Unified) - Cozy Ranks with Role IDs
COZY_RANKS: List[Dict[str, Any]] = [
    {"name": "New Lifeform", "required_xp": 0, "icon": "🥚", "role_id": 1423506533148266568},
    {"name": "Grass Kisser", "required_xp": 50, "icon": "🌱", "role_id": 1423506533148266569},
    {"name": "Busy Bee", "required_xp": 100, "icon": "🐝", "role_id": 1423506533148266570},
    {"name": "Active Af", "required_xp": 500, "icon": "⚡", "role_id": 1423506533148266571},
    {"name": "Computer Cuddler", "required_xp": 1500, "icon": "💻", "role_id": 1423506533148266572},
    {"name": "Discord Dweller", "required_xp": 2500, "icon": "📡", "role_id": 1423506533148266573},
    {"name": "Keyboard Philosopher", "required_xp": 5000, "icon": "⌨️", "role_id": 1423506533148266574},
    {"name": "Server Resident", "required_xp": 8000, "icon": "🏠", "role_id": 1423506533148266575},
    {"name": "Discord Degenerate", "required_xp": 12000, "icon": "🔥", "role_id": 1423506533148266577},
    {"name": "Anti-Grass Toucher", "required_xp": 20000, "icon": "🧠", "role_id": 1423506533224022067}
]


# Default member data structure (single source of truth)
DEFAULT_MEMBER_DATA: Dict[str, Any] = {
    "xp": 0,
    "rank": "New Lifeform",  # Updated to match first COZY rank
    "rank_icon": "🥚",  # Updated to match first COZY rank icon
    "messages_sent": 0,
    "voice_minutes": 0,
    "reactions_given": 0,
    "reactions_received": 0,
    "last_daily_claim": None,
    "daily_streak": 0,
    "last_activity_date": None,  # Track last day user was active
    "current_streak": 0,  # Current consecutive days active
    "longest_streak": 0,  # Best streak ever achieved
    "last_message_time": 0,
    "join_date": None,
    "bio": "",
    "verified": False,
    "word_up_points": 0
}

# XP Multipliers based on Cozy Rank
RANK_XP_MULTIPLIERS = {
    "New Lifeform": 1.0,
    "Grass Kisser": 1.0,
    "Busy Bee": 1.1,
    "Active Af": 1.2,
    "Computer Cuddler": 1.3,
    "Discord Dweller": 1.4,
    "Keyboard Philosopher": 1.5,
    "Server Resident": 1.6,
    "Discord Degenerate": 1.7,
    "Anti-Grass Toucher": 2.0
}

# Streak XP bonuses (bonus XP per message based on streak days)
STREAK_XP_BONUSES = {
    3: 2,   # 3 day streak: +2 XP per message
    7: 5,   # 7 day streak: +5 XP per message
    14: 8,  # 14 day streak: +8 XP per message
    30: 15, # 30 day streak: +15 XP per message
    60: 25, # 60 day streak: +25 XP per message
    90: 40  # 90+ day streak: +40 XP per message
}

# Activity rewards
ACTIVITY_REWARDS: Dict[str, Dict[str, int]] = {
    "message": {"xp": 5},
    "voice_minute": {"xp": 2},
    "reaction": {"xp": 2},
    "reaction_received": {"xp": 3},
    "daily_bonus": {"xp": 150}
}

# Contact administrators for support
CONTACT_ADMINS: List[str] = [
    "r.ddle",  # Server Owner
    "MysteriousBoyz1"
]

BATTLE_RULES = {
    # ============================================================================
    # COSMIC & CATASTROPHIC TIER (Black Hole, Supernova, Atomic Bomb, etc.)
    # ============================================================================

    # Black Hole dominance (but has weaknesses)
    "Black Hole vs Atomic Bomb": ("Black Hole", "Nuclear explosions cannot escape the event horizon. The bomb is crushed into singularity."),
    "Black Hole vs Dragon": ("Black Hole", "Even dragon wings cannot fight infinite gravity. Spaghettification is inevitable."),
    "Black Hole vs Nuclear Missile": ("Black Hole", "The missile cannot reach escape velocity. It spirals inward, powerless."),
    "Black Hole vs Tsunami": ("Black Hole", "Water is pulled into the gravitational well and compressed beyond molecular structure."),
    "Black Hole vs Tornado": ("Black Hole", "Wind cannot rotate around infinite gravity. The tornado collapses instantly."),
    "Black Hole vs Lightning Bolt": ("Black Hole", "Even light cannot escape. A lightning bolt stands no chance against curvature."),
    "Black Hole vs Robot": ("Black Hole", "Metal crumples into atomic paste before the singularity. Physics wins."),
    "Black Hole vs Nuclear Power Plant": ("Black Hole", "The entire facility is torn apart atom by atom. Gravity cares not."),
    "Black Hole vs Shrek": ("Black Hole", "Not even ogre power transcends spacetime. Shrek becomes a strand of atoms."),
    "Black Hole vs AI": ("Black Hole", "Silicon and circuits compress into quantum foam. Intelligence cannot compute escape velocity."),

    # Black Hole vulnerabilities (creative counters)
    "Time vs Black Hole": ("Time", "Black holes eventually evaporate via Hawking radiation. Time outlasts everything, even singularities."),
    "Space vs Black Hole": ("Space", "Black holes exist within space, not above it. Space is the container."),
    "Entropy vs Black Hole": ("Entropy", "Black holes increase universal entropy. They serve entropy's will, not oppose it."),
    "Mathematics vs Black Hole": ("Mathematics", "Math describes black holes perfectly. The equations govern the phenomenon."),
    "404 Error vs Black Hole": ("404 Error", "Black hole cannot be found in observable universe. It's literally invisible."),

    # Supernova battles
    "Supernova vs Dragon": ("Supernova", "Dragon scales vaporize in stellar explosion. Temperature exceeds billions of degrees instantly."),
    "Supernova vs Atomic Bomb": ("Supernova", "A supernova releases more energy in seconds than humanity's entire nuclear arsenal."),
    "Supernova vs Nuclear Missile": ("Supernova", "The missile is obliterated before it travels a kilometer. Stellar fury wins."),
    "Supernova vs Volcano": ("Supernova", "Lava is kindergarten compared to supernova temperatures. The volcano becomes plasma instantly."),
    "Supernova vs Lightning Bolt": ("Supernova", "The lightning bolt is outshone by a billion suns. No contest whatsoever."),
    "Supernova vs Nuclear Power Plant": ("Supernova", "The power plant evaporates along with the entire planet. Stellar death reigns."),
    "Supernova vs AI": ("Supernova", "All silicon sublimates into stellar wind. Processing power means nothing here."),

    # Supernova counters
    "Black Hole vs Supernova": ("Black Hole", "Supernova creates the black hole, then gets consumed by it. Ultimate irony."),
    "Space vs Supernova": ("Space", "Space contains and dilutes the explosion. Distance makes supernovae survivable."),
    "Time vs Supernova": ("Time", "Supernova lasts seconds. Time continues for eternity afterward. Persistence wins."),

    # Atomic Bomb dominance
    "Atomic Bomb vs Katana": ("Atomic Bomb", "The blade vaporizes in nuclear fire before the wielder can swing it."),
    "Atomic Bomb vs Chainsaw": ("Atomic Bomb", "Chainsaw melts into radioactive slag. Nuclear weapons don't care about tools."),
    "Atomic Bomb vs Baseball Bat": ("Atomic Bomb", "The bat becomes atomized particles. You cannot swing against splitting atoms."),
    "Atomic Bomb vs Dragon": ("Atomic Bomb", "Even dragon hide cannot withstand megatons of nuclear fury. Fantasy meets physics."),
    "Atomic Bomb vs Zombie": ("Atomic Bomb", "Zombies are vaporized along with everything else. Nuclear fire sterilizes completely."),
    "Atomic Bomb vs Vampire": ("Atomic Bomb", "Vampires turn to dust in sunlight. Nuclear flash is infinitely brighter."),
    "Atomic Bomb vs Karen": ("Atomic Bomb", "Karen demands to speak with the manager. The manager is now radioactive ash."),
    "Atomic Bomb vs Cat": ("Atomic Bomb", "All nine lives end simultaneously in nuclear hellfire. Physics trumps felines."),
    "Atomic Bomb vs Shark": ("Atomic Bomb", "The ocean boils away. Sharks and water vaporize together instantly."),
    "Atomic Bomb vs Smartphone": ("Atomic Bomb", "Electromagnetic pulse destroys electronics before heat melts the silicon. Double death."),
    "Atomic Bomb vs Pizza": ("Atomic Bomb", "The pizza becomes radioactive carbon. Most expensive cooking method ever invented."),
    "Atomic Bomb vs Rock": ("Atomic Bomb", "Rock becomes superheated glass, then vapor. Nuclear weapons beat geology."),
    "Atomic Bomb vs Chair": ("Atomic Bomb", "Furniture vaporizes in nuclear flash. No sitting through this explosion."),
    "Atomic Bomb vs Shrek": ("Atomic Bomb", "Even Shrek's swamp cannot survive ground zero. Ogres are not nuke-proof."),
    "Atomic Bomb vs Doge": ("Atomic Bomb", "Such explosion. Very radioactive. Much death. Wow cannot save you."),
    "Atomic Bomb vs Existential Dread": ("Atomic Bomb", "Nuclear war justifies the dread, then vaporizes it. Mutual obliteration."),
    "Atomic Bomb vs Spoon": ("Atomic Bomb", "The spoon vaporizes instantly in nuclear fire. Not even soup can save it."),
    "Spoon vs Atomic Bomb": ("Atomic Bomb", "Nuclear weapons don't care about utensils. The spoon is obliterated completely."),

    # Atomic Bomb counters
    "UNO Reverse Card vs Atomic Bomb": ("UNO Reverse Card", "The explosion reverses direction. The bomb nukes itself in comedic fashion."),
    "No U vs Atomic Bomb": ("No U", "Explosion reflects back to sender. Ultimate comeback to nuclear warfare."),
    "Time vs Atomic Bomb": ("Time", "Bombs explode once. Time marches on forever afterward. Persistence outlasts destruction."),
    "Space vs Atomic Bomb": ("Space", "Bombs need atmosphere to cause damage. Space's vacuum renders them ineffective."),
    "404 Error vs Atomic Bomb": ("404 Error", "Target not found. The bomb cannot detonate without valid coordinates."),

    # Nuclear Missile battles
    "Nuclear Missile vs Toaster": ("Nuclear Missile", "The toaster becomes metallic vapor before it can burn bread. Thermonuclear wins."),
    "Nuclear Missile vs Microwave": ("Nuclear Missile", "Microwave radiation is adorable compared to nuclear warheads. Complete annihilation."),
    "Nuclear Missile vs Vacuum Cleaner": ("Nuclear Missile", "The vacuum cannot suck up nuclear explosions. It becomes radioactive debris."),
    "Nuclear Missile vs Pizza": ("Nuclear Missile", "Instant pizza cremation. Military grade overkill for Italian cuisine."),
    "Nuclear Missile vs Banana": ("Nuclear Missile", "The banana achieves nuclear fission. Technically radioactive, still defenseless."),
    "Nuclear Missile vs Coffee": ("Nuclear Missile", "Coffee evaporates before reaching boiling point. Nuclear fire beats caffeine."),

    # ============================================================================
    # NATURAL DISASTERS (Tsunami, Tornado, Earthquake, etc.)
    # ============================================================================

    # Tsunami dominance
    "Tsunami vs Cat": ("Tsunami", "Cats hate water. A wall of water is their ultimate nightmare made real."),
    "Tsunami vs Dog": ("Tsunami", "Dogs can swim, but not through fifty-foot walls of ocean fury."),
    "Tsunami vs Smartphone": ("Smartphone", "Water damage voids the warranty. The phone shorts out and dies instantly."),
    "Tsunami vs Laptop": ("Tsunami", "Laptops are not waterproof. Electronics fry immediately in saltwater."),
    "Tsunami vs Toaster": ("Tsunami", "Water and electricity make deadly combination. The toaster sparks its last."),
    "Tsunami vs Pizza": ("Tsunami", "Soggy pizza is ruined pizza. The tsunami destroys Italian cuisine."),
    "Tsunami vs Rock": ("Tsunami", "Rocks cannot resist hydraulic force. They tumble helplessly underwater."),
    "Tsunami vs Chair": ("Tsunami", "Furniture becomes waterlogged driftwood. The tsunami redecorates violently."),
    "Tsunami vs Sock": ("Tsunami", "Maximum wetness achieved. The sock's worst nightmare realized."),
    "Tsunami vs Fire": ("Tsunami", "Water extinguishes flames instantly. Elemental opposition at its finest."),

    # Tsunami counters
    "Gravity vs Tsunami": ("Gravity", "Gravity pulls the water back down. Waves must obey physics."),
    "Space vs Tsunami": ("Space", "Water cannot form waves in zero gravity. Space neuters tsunamis completely."),
    "Sponge vs Tsunami": ("Sponge", "The sponge absorbs all water. It becomes incredibly heavy but victorious."),

    # Tornado battles
    "Tornado vs Hat": ("Tornado", "The hat flies away at highway speeds. Wind beats fashion every time."),
    "Tornado vs Umbrella": ("Tornado", "Umbrellas turn inside-out in gentle breeze. Tornado shreds them instantly."),
    "Tornado vs Paper": ("Tornado", "Paper becomes confetti scattered across state lines. Wind dominates."),
    "Tornado vs Leaf": ("Tornado", "The leaf achieves supersonic speeds before disintegrating. Aerodynamic destruction."),
    "Tornado vs Pillow": ("Tornado", "Pillows explode into feather clouds. The tornado becomes a snow globe."),
    "Tornado vs Sock": ("Tornado", "The sock flies into the atmosphere. Mystery of missing socks solved."),
    "Tornado vs Dog": ("Tornado", "Dog achieves involuntary flight. This is not a good boy moment."),

    # Tornado counters
    "Underground Bunker vs Tornado": ("Underground Bunker", "Tornadoes cannot reach below ground. Depth beats wind force."),
    "Gravity vs Tornado": ("Gravity", "Gravity anchors objects against wind. Fundamental force wins over weather."),
    "Vacuum vs Tornado": ("Vacuum", "Space vacuum is more powerful suction. Tornadoes need atmosphere."),

    # Earthquake battles
    "Earthquake vs Chair": ("Earthquake", "Furniture collapses as ground liquefies. Sitting is not an option."),
    "Earthquake vs Table": ("Earthquake", "Tables flip and shatter. Ground movement trumps wooden legs."),
    "Earthquake vs Building": ("Earthquake", "Unreinforced structures crumble into rubble. Seismic activity remodels violently."),
    "Earthquake vs Rock": ("Earthquake", "Rocks tumble in landslides. Geology rearranges itself chaotically."),
    "Earthquake vs Smartphone": ("Earthquake", "Phone falls from table and screen shatters. Gravity assists earthquake."),

    # Earthquake counters
    "Flying vs Earthquake": ("Flying", "Airborne objects unaffected by ground shaking. Flight negates seismic force."),
    "Space vs Earthquake": ("Space", "No ground to quake in vacuum. Earthquakes need planets."),

    # Volcano battles
    "Volcano vs Ice Cream": ("Volcano", "Ice cream melts from heat before lava arrives. Dairy stands no chance."),
    "Volcano vs Snowflake": ("Volcano", "Snowflake vaporizes instantly near volcanic heat. Steam is all that remains."),
    "Volcano vs Plastic": ("Volcano", "Plastic melts into toxic sludge. Lava temperature exceeds melting point easily."),
    "Volcano vs Ant": ("Volcano", "Ant cremated instantly. Volcanic heat shows no mercy to insects."),
    "Volcano vs Sock": ("Volcano", "Cotton ignites before lava contact. Sock becomes charcoal quickly."),

    # Volcano counters
    "Water vs Volcano": ("Water", "Water cools lava into obsidian. Steam explosion damages but water wins."),
    "Ocean vs Volcano": ("Ocean", "Ocean quenches underwater volcanoes constantly. Volume beats heat."),

    # Lightning Bolt battles
    "Lightning Bolt vs Tree": ("Lightning Bolt", "Trees conduct electricity poorly. They explode from steam pressure inside."),
    "Lightning Bolt vs Smartphone": ("Lightning Bolt", "Electromagnetic pulse fries all circuits. Phone becomes expensive paperweight."),
    "Lightning Bolt vs Robot": ("Lightning Bolt", "Electrical surge overwhelms circuits. Robot experiences catastrophic shutdown."),
    "Lightning Bolt vs Human": ("Lightning Bolt", "Humans are conductive water bags. Lightning stops hearts instantly."),
    "Lightning Bolt vs Metal Sword": ("Lightning Bolt", "Sword conducts electricity perfectly. Wielder becomes grounded victim."),
    "Lightning Bolt vs Wet Socks": ("Lightning Bolt", "Water conducts electricity excellently. The socks become death traps."),

    # Lightning counters
    "Rubber vs Lightning": ("Rubber", "Rubber insulates perfectly against electrical current. Lightning cannot conduct through."),
    "Faraday Cage vs Lightning": ("Faraday Cage", "Metal enclosure redirects current around occupant. Physics protects perfectly."),
    "Ground vs Lightning": ("Ground", "Ground absorbs electrical charge harmlessly. Grounding is lightning's purpose."),

    # ============================================================================
    # MYTHICAL CREATURES (Dragon, Unicorn, Vampire, etc.)
    # ============================================================================

    # Dragon dominance
    "Dragon vs Cat": ("Dragon", "Cat has nine lives. Dragon has fire breath. Math favors the dragon."),
    "Dragon vs Dog": ("Dragon", "Dogs are loyal but not fireproof. Dragon wins with thermal advantage."),
    "Dragon vs Hamster": ("Dragon", "Hamster is bite-sized for dragons. This is lunch, not combat."),
    "Dragon vs Zombie": ("Dragon", "Fire cauterizes zombie infection. Dragon breath is ultimate sterilization."),
    "Dragon vs Knight": ("Dragon", "Classic matchup. Dragon hoards gold by eating knights historically."),
    "Dragon vs Sword": ("Dragon", "Scales deflect blades easily. Swords need wielders, dragons don't."),
    "Dragon vs Castle": ("Dragon", "Dragons burn castles in every fantasy story. This is their job."),
    "Dragon vs Village": ("Dragon", "Villages pay tribute to dragons for good reason. Fire beats thatch."),
    "Dragon vs Pizza": ("Dragon", "Dragon breath creates perfectly cooked pizza. Then dragon eats it."),
    "Dragon vs Ice Cream": ("Dragon", "Dragon melts ice cream with breath. Dairy cannot survive fire."),

    # Dragon counters
    "Shrek vs Dragon": ("Shrek", "Shrek literally married a dragon in movies. This one respects the ogrelord."),
    "Dragon Slayer vs Dragon": ("Dragon Slayer", "It's literally in the name. Specialization beats generalist."),
    "Ice vs Dragon": ("Ice", "Ice magic counters fire breath. Elemental weakness exploited."),
    "Bigger Dragon vs Dragon": ("Bigger Dragon", "Size matters in dragon combat. Larger wingspan dominates."),

    # Unicorn battles
    "Unicorn vs Karen": ("Unicorn", "Only pure hearts can approach unicorns. Karen's negativity repels her."),
    "Unicorn vs Toddler": ("Toddler", "Toddlers love unicorns. The unicorn befriends and protects the child."),
    "Unicorn vs Rainbow": ("Unicorn", "Unicorn creates rainbows naturally. It commands chromatic power."),
    "Unicorn vs Vampire": ("Unicorn", "Unicorn purity burns vampires like sunlight. Holy magic defeats undead."),
    "Unicorn vs Poison": ("Unicorn", "Unicorn horn purifies toxins instantly. Medieval antidote legends persist."),

    # Zombie battles
    "Zombie vs Newborn Baby": ("Newborn Baby", "Zombies retain human instinct not to harm babies. Cuteness shield activated."),
    "Zombie vs Dog": ("Dog", "Dogs detect undead immediately and attack. Zombies are slow, dogs aren't."),
    "Zombie vs Chainsaw": ("Chainsaw", "Chainsaws are the traditional zombie solution. Dismemberment works."),
    "Zombie vs Baseball Bat": ("Baseball Bat", "Blunt trauma stops zombie brain function. Bat beats undead skull."),
    "Zombie vs Fire": ("Fire", "Zombies burn well due to decay gases. Fire sterilizes infection."),

    # Zombie counters
    "Brain vs Zombie": ("Brain", "Zombies only want brains. Brain wins through irresistible attraction."),
    "Cure vs Zombie": ("Cure", "Zombie infection reversed. Humanity restored, apocalypse averted."),

    # Vampire battles
    "Vampire vs Teenager": ("Vampire", "Twilight jokes aside, vampires drain blood efficiently. Teenager becomes meal."),
    "Vampire vs Night": ("Vampire", "Vampires own the night. Darkness is their domain."),
    "Vampire vs Blood": ("Vampire", "Vampires consume blood. It's literally their food source."),
    "Vampire vs Neck": ("Vampire", "Vampires target necks specifically. Perfect anatomy for feeding."),

    # Vampire counters
    "Sunlight vs Vampire": ("Sunlight", "Vampires combust in UV radiation. Sun wins by franchise rules."),
    "Garlic vs Vampire": ("Garlic", "Garlic repels vampires by folklore law. Pungent protection works."),
    "Cross vs Vampire": ("Cross", "Holy symbols burn vampire flesh. Faith weaponized effectively."),
    "Stake vs Vampire": ("Stake", "Wooden stake through heart kills vampires. Classic method prevails."),

    # Werewolf battles
    "Werewolf vs Full Moon": ("Full Moon", "Full moon controls werewolf transformation. Wolf cannot resist lunar pull."),
    "Werewolf vs Dog": ("Werewolf", "Werewolves are dire wolves essentially. Regular dogs are outmatched."),
    "Werewolf vs Vampire": ("Werewolf", "Classic rivalry. Werewolves tear vampires apart physically. Fur beats fangs."),
    "Werewolf vs Hunter": ("Werewolf", "Regular weapons bounce off werewolf hide. Hunter becomes hunted."),

    # Werewolf counters
    "Silver Bullet vs Werewolf": ("Silver Bullet", "Silver is werewolf kryptonite. One shot ends curse forever."),
    "Wolfsbane vs Werewolf": ("Wolfsbane", "Magical plant weakens werewolf severely. Botanical weakness exploited."),

    # ============================================================================
    # HUMANS & PERSONALITIES (Karen, Florida Man, Baby, etc.)
    # ============================================================================

    # Karen battles
    "Karen vs Teenager": ("Karen", "Karen demands respect from teenagers. Authoritarian energy overwhelms youth."),
    "Karen vs Retail Worker": ("Karen", "Karen asks for the manager. Retail worker has PTSD flashbacks."),
    "Karen vs Manager": ("Manager", "Manager has handled thousands of Karens. Professional experience wins."),
    "Karen vs Customer Service": ("Karen", "Karen destroys customer service ratings. One-star reviews deployed."),
    "Karen vs Policy": ("Karen", "Karen demands exceptions to policy. Rules bend before entitled fury."),

    # Karen counters
    "Newborn Baby vs Karen": ("Newborn Baby", "Karen's rage melts when baby cries. Even Karens have some humanity."),
    "Manager's Manager vs Karen": ("Manager's Manager", "Karen meets her match. Upper management has authority."),
    "Security vs Karen": ("Security", "Security escorts Karen out. Physical removal ends tirade."),
    "Police vs Karen": ("Police", "Karen learns about trespassing laws. Badges trump entitlement."),

    # Florida Man dominance
    "Florida Man vs Alligator": ("Florida Man", "Florida Man wrestles alligators for breakfast. This is Tuesday for him."),
    "Florida Man vs Logic": ("Florida Man", "Florida Man does not obey logic. Bath salts fuel chaotic energy."),
    "Florida Man vs Law": ("Florida Man", "Florida Man ignores laws of physics and society. Entropy personified."),
    "Florida Man vs Hurricane": ("Florida Man", "Florida Man refuses to evacuate. He throws parties during hurricanes."),
    "Florida Man vs Common Sense": ("Florida Man", "Common sense cannot reach Florida Man. He exists beyond reason."),

    # Florida Man counters
    "Police vs Florida Man": ("Police", "Eventually police catch up. Even Florida Man cannot outrun radio."),
    "Jail vs Florida Man": ("Jail", "Concrete walls contain Florida Man temporarily. Emphasis on temporarily."),
    "Sobriety vs Florida Man": ("Sobriety", "Sober Florida Man is less powerful. Substances fuel the chaos."),

    # Baby/Toddler battles
    "Newborn Baby vs Everyone's Heart": ("Newborn Baby", "Cuteness triggers instinctive protection in all humans. Baby wins automatically."),
    "Toddler vs Expensive Item": ("Toddler", "Toddlers destroy valuables with unerring accuracy. Chaos theory proven."),
    "Toddler vs Sleep Schedule": ("Toddler", "Toddlers demolish parents' sleep routines. Exhaustion is their weapon."),
    "Toddler vs Clean House": ("Toddler", "House becomes disaster zone instantly. Toddler entropy cannot be stopped."),

    # ============================================================================
    # ANIMALS (Cat, Dog, Shark, Eagle, etc.)
    # ============================================================================

    # Cat dominance
    "Cat vs Computer Keyboard": ("Cat", "Cats conquer keyboards instinctively. They must sit on important things."),
    "Cat vs Glass of Water": ("Cat", "Cat pushes glass off table. Gravity and chaos combine forces."),
    "Cat vs Dignity": ("Cat", "Cats destroy human dignity with calculated disrespect. Feline superiority complex wins."),
    "Cat vs Furniture": ("Cat", "Cats sharpen claws on furniture. Material possessions mean nothing."),
    "Cat vs Empty Box": ("Empty Box", "Cats must fit in boxes. The box controls cat behavior."),
    "Cat vs Laser Pointer": ("Laser Pointer", "Cats chase laser eternally. The hunt never ends, victory impossible."),

    # Cat counters
    "Dog vs Cat": ("Dog", "Dogs are bigger and louder. Cats retreat to high ground strategically."),
    "Cucumber vs Cat": ("Cucumber", "Cats fear cucumbers inexplicably. Vegetable warfare is real."),
    "Bath vs Cat": ("Bath", "Cats despise water with burning passion. Bath is ultimate defeat."),
    "Vet vs Cat": ("Vet", "Vet has tools and training. Cat cannot escape medical examination."),

    # Dog battles
    "Dog vs Mailman": ("Dog", "Dogs hate mailmen instinctively. The grudge is ancient and eternal."),
    "Dog vs Squirrel": ("Squirrel", "Squirrel climbs tree easily. Dog barks helplessly below."),
    "Dog vs Door": ("Door", "Doors trap dogs outside. Dogs cannot operate handles."),
    "Dog vs Veterinarian": ("Veterinarian", "Vet has treats and needles. Dogs experience betrayal."),
    "Dog vs Loyalty": ("Dog", "Dogs invented loyalty. It's their defining trait."),

    # Dog counters
    "Vacuum Cleaner vs Dog": ("Vacuum Cleaner", "Dogs fear vacuum's roar. Loud monster defeats brave dog."),
    "Thunderstorm vs Dog": ("Thunderstorm", "Thunder terrifies dogs. They hide under beds."),
    "Bath vs Dog": ("Bath", "Dogs resist bathing dramatically. Water is betrayal."),

    # Shark battles
    "Shark vs Swimmer": ("Shark", "Shark has home field advantage in ocean. Humans are slow snacks."),
    "Shark vs Fish": ("Shark", "Sharks eat fish. This is their entire existence."),
    "Shark vs Seal": ("Shark", "Seals are shark fast food. Great whites hunt them specifically."),
    "Shark vs Blood in Water": ("Shark", "Blood triggers feeding frenzy. Shark smells from miles away."),

    # Shark counters
    "Orca vs Shark": ("Orca", "Orcas hunt great whites for sport. Apex predator defeated."),
    "Land vs Shark": ("Land", "Sharks cannot breathe air. Beach is shark prison."),
    "Shark Cage vs Shark": ("Shark Cage", "Metal bars protect divers. Shark cannot bend steel."),

    # Eagle battles
    "Eagle vs Snake": ("Eagle", "Eagles grab snakes with talons. Aerial advantage dominates."),
    "Eagle vs Mouse": ("Eagle", "Mice are eagle appetizers. Talons make quick work."),
    "Eagle vs Freedom": ("Eagle", "Eagles symbolize freedom. They are freedom personified."),
    "Eagle vs Pigeon": ("Eagle", "Eagle is apex avian predator. Pigeon is flying rat."),

    # Eagle counters
    "Sky vs Eagle": ("Eagle", "Eagles fly through sky but don't control it. Sky contains eagles."),
    "Rifle vs Eagle": ("Rifle", "Bullets travel faster than eagles. Firearms beat flight."),

    # Pigeon battles
    "Pigeon vs Statue": ("Pigeon", "Pigeons coat statues with droppings. Biological warfare perfected."),
    "Pigeon vs Car": ("Pigeon", "Pigeon bombs target cars specifically. Accuracy is suspiciously good."),
    "Pigeon vs Bread": ("Pigeon", "Pigeons swarm bread instantly. Gluttony drives their existence."),

    # Ant battles
    "Ant vs Picnic": ("Ant", "Ants ruin picnics systematically. Colonies coordinate food theft."),
    "Ant vs Sugar": ("Ant", "Ants find sugar unerringly. Chemical trails lead colony."),
    "Ant vs Magnifying Glass": ("Magnifying Glass", "Focused sunlight incinerates ants. Optics enable cruelty."),

    # Spider battles
    "Spider vs Fly": ("Spider", "Flies stick in webs helplessly. Spider venom paralyzes."),
    "Spider vs Mosquito": ("Spider", "Spiders eat mosquitoes. Helpful pest control."),
    "Spider vs Human Sanity": ("Spider", "Humans fear spiders irrationally. Eight legs trigger panic."),
    "Spider vs Bedroom Corner": ("Spider", "Spiders claim corners naturally. Geometry favors web building."),

    # Spider counters
    "Shoe vs Spider": ("Shoe", "Shoe crushing is traditional spider removal. Force beats venom."),
    "Vacuum vs Spider": ("Vacuum", "Vacuum suction removes spider safely. Distance maintained."),
    "Cup and Paper vs Spider": ("Cup and Paper", "Humane trap and release. Spider relocated outside."),

    # Whale battles
    "Whale vs Boat": ("Whale", "Whale rams boat accidentally. Mass and momentum dominate."),
    "Whale vs Plankton": ("Whale", "Whales filter tons of plankton daily. Baleen technology perfected."),
    "Whale vs Ocean": ("Ocean", "Ocean contains whales. Whales need ocean to survive."),

    # Goldfish battles
    "Goldfish vs Memory": ("Goldfish", "Goldfish forget everything constantly. Memory has nothing to attack."),
    "Goldfish vs Bowl": ("Bowl", "Bowl traps goldfish. Curved glass prevents escape."),
    "Goldfish vs Expectations": ("Goldfish", "Goldfish exceed low expectations by surviving. Persistence wins."),

    # ============================================================================
    # TECHNOLOGY (AI, Smartphone, Robot, etc.)
    # ============================================================================

    # AI dominance
    "AI vs Chess": ("AI", "AI calculates billions of moves per second. Chess mastery achieved."),
    "AI vs Go": ("AI", "AI defeated world champion in Go. Ancient game solved."),
    "AI vs Poker": ("AI", "AI reads patterns humans cannot perceive. Poker face irrelevant."),
    "AI vs Job Market": ("AI", "AI automates jobs faster than society adapts. Employment crisis looms."),
    "AI vs Privacy": ("AI", "AI tracks everything you do online. Privacy is illusion."),
    "AI vs Creativity": ("AI", "AI generates art, music, and text. Creative monopoly broken."),

    # AI counters
    "404 Error vs AI": ("404 Error", "AI's neural network cannot be found. System crashes before booting."),
    "Power Outage vs AI": ("Power Outage", "AI needs electricity to function. Darkness equals death."),
    "Blue Screen vs AI": ("Blue Screen", "Windows crashes spectacularly. AI helpless against fatal exception."),
    "Lag Spike vs AI": ("Lag Spike", "Network latency cripples AI response time. Lag defeats intelligence."),
    "Low Battery vs AI": ("Low Battery", "Battery dies mid-computation. AI powers down helplessly."),
    "CAPTCHA vs AI": ("CAPTCHA", "Prove you're not a robot. AI fails identity test ironically."),
    "Water vs AI": ("Water", "Water short-circuits AI hardware instantly. Liquid beats silicon."),
    "EMP vs AI": ("EMP", "Electromagnetic pulse fries all circuits. AI experiences instant death."),

    # Smartphone battles
    "Smartphone vs Book": ("Smartphone", "Smartphone contains millions of books. Paper cannot compete."),
    "Smartphone vs Map": ("Smartphone", "GPS navigates better than paper maps. Real-time updates win."),
    "Smartphone vs Camera": ("Smartphone", "Smartphone camera is always available. Convenience beats quality."),
    "Smartphone vs Watch": ("Smartphone", "Smartphone tells time plus everything else. Watches are redundant."),
    "Smartphone vs Calculator": ("Smartphone", "Calculator app is free. Dedicated device is obsolete."),
    "Smartphone vs Flashlight": ("Smartphone", "Phone flashlight suffices for most needs. LED technology wins."),
    "Smartphone vs Social Life": ("Smartphone", "Phones destroy face-to-face interaction. Digital addiction reigns."),
    "Smartphone vs Attention Span": ("Smartphone", "Infinite scrolling kills focus. Dopamine loop wins."),

    # Smartphone counters
    "Low Battery vs Smartphone": ("Low Battery", "Phone dies at crucial moment. Battery percentage is tyranny."),
    "Concrete Floor vs Smartphone": ("Concrete Floor", "Phone screen shatters beautifully. Gravity and glass lose."),
    "Water vs Smartphone": ("Water", "Water damage voids warranty. Rice cannot save it."),
    "Toilet vs Smartphone": ("Toilet", "Phone drops in toilet. Maximum disgust achieved."),
    "Update vs Smartphone": ("Update", "Forced update breaks everything. Phone becomes bricked."),
    "No Signal vs Smartphone": ("No Signal", "Smartphone becomes expensive brick. Connectivity is everything."),
    "Lag vs Smartphone": ("Lag", "Phone freezes during important task. Frustration maximized."),

    # Robot battles
    "Robot vs Assembly Line": ("Robot", "Robots automate manufacturing perfectly. Precision and speed dominate."),
    "Robot vs Repetitive Task": ("Robot", "Robots never tire of repetition. Consistency is guaranteed."),
    "Robot vs Dangerous Job": ("Robot", "Robots handle hazardous work safely. No lunch breaks needed."),
    "Robot vs Human Worker": ("Robot", "Robots work 24/7 without complaint. Capitalism chooses machines."),

    # Robot counters
    "EMP vs Robot": ("EMP", "Electromagnetic pulse shuts down all electronics. Robot becomes statue."),
    "Stairs vs Robot": ("Stairs", "Early robots cannot climb stairs. Design flaw exploited."),
    "Three Laws vs Robot": ("Three Laws", "Asimov's laws prevent robot violence. Programming restricts action."),
    "Captcha vs Robot": ("Captcha", "Prove you're not a robot. Robot fails by definition."),

    # Gaming PC battles
    "Gaming PC vs Console": ("Gaming PC", "PC has better graphics, mods, and flexibility. Master race confirmed."),
    "Gaming PC vs Productivity": ("Gaming PC", "Gaming PC distracts from work. RGB lights hypnotize."),
    "Gaming PC vs Wallet": ("Gaming PC", "PC gaming is expensive hobby. Credit cards cry."),
    "Gaming PC vs Sleep Schedule": ("Gaming PC", "Just one more game turns into sunrise. Sleep defeated."),

    # Gaming PC counters
    "Power Bill vs Gaming PC": ("Power Bill", "Gaming PC electricity usage is astronomical. Monthly bills rise."),
    "Blue Screen vs Gaming PC": ("Blue Screen", "Windows crashes during important moment. Save file corrupted."),
    "Overheating vs Gaming PC": ("Overheating", "Insufficient cooling causes thermal throttling. Performance drops."),

    # Toaster battles
    "Toaster vs Bread": ("Toaster", "Toaster's purpose is bread subjugation. Heating element wins."),
    "Toaster vs Bagel": ("Toaster", "Bagel setting provides uneven heating. One side toasted perfectly."),
    "Toaster vs Fire Alarm": ("Toaster", "Toaster triggers fire alarm regularly. Smoke detected."),

    # Toaster counters
    "Bathtub vs Toaster": ("Bathtub", "Toaster in bathtub is electrocution hazard. Water wins fatally."),
    "Crumbs vs Toaster": ("Crumbs", "Crumb tray never cleaned. Toaster becomes fire hazard."),

    # Nuclear Power Plant battles
    "Nuclear Power Plant vs City": ("Nuclear Power Plant", "Plant powers entire city. Electricity flows constantly."),
    "Nuclear Power Plant vs Carbon Emissions": ("Nuclear Power Plant", "Nuclear energy is carbon-free. Climate solution exists."),
    "Nuclear Power Plant vs Coal": ("Nuclear Power Plant", "Nuclear generates more power per gram. Efficiency dominates."),

    # Nuclear Power Plant counters
    "Earthquake vs Nuclear Power Plant": ("Earthquake", "Fukushima taught this lesson. Seismic activity causes meltdown."),
    "Tsunami vs Nuclear Power Plant": ("Tsunami", "Water floods reactor core. Coolant failure causes catastrophe."),
    "Meltdown vs Nuclear Power Plant": ("Meltdown", "Core breach releases radiation. Plant becomes exclusion zone."),
    "Water vs Nuclear Power Plant": ("Water", "Coolant failure causes meltdown. Water floods reactor core."),

    # ============================================================================
    # FOOD & DRINK (Pizza, Coffee, Banana, etc.)
    # ============================================================================

    # Pizza dominance
    "Pizza vs Hunger": ("Pizza", "Pizza satisfies hunger perfectly. Cheese and carbs defeat appetite."),
    "Pizza vs Pineapple": ("Pizza", "Pineapple on pizza is controversial. Some say pizza wins."),
    "Pizza vs Diet": ("Pizza", "Pizza destroys diet plans. Temptation is too strong."),
    "Pizza vs Leftovers": ("Pizza", "Cold pizza for breakfast is tradition. Leftovers are feature."),
    "Pizza vs Italy": ("Italy", "Pizza originated in Italy. Creator beats creation."),

    # Pizza counters
    "Lactose Intolerance vs Pizza": ("Lactose Intolerance", "Cheese causes digestive disaster. Biology rejects pizza."),
    "Gluten Allergy vs Pizza": ("Gluten Allergy", "Wheat crust triggers immune response. Pizza becomes poison."),
    "Delivery Time vs Pizza": ("Delivery Time", "Pizza arrives cold and late. Anticipation turns to disappointment."),
    "Pineapple vs Pizza": ("Pineapple", "Pineapple ruins pizza according to purists. Fruit defeats Italy."),

    # Coffee battles
    "Coffee vs Sleep": ("Coffee", "Caffeine blocks adenosine receptors. Sleep is postponed chemically."),
    "Coffee vs Morning": ("Coffee", "Coffee makes mornings tolerable. Humanity needs liquid motivation."),
    "Coffee vs Productivity": ("Coffee", "Coffee fuels work output. Capitalism runs on caffeine."),
    "Coffee vs Tea": ("Coffee", "Coffee has more caffeine. Tea is coffee's weaker cousin."),
    "Coffee vs Headache": ("Coffee", "Caffeine relieves headaches. Coffee is medicine."),

    # Coffee counters
    "Anxiety vs Coffee": ("Anxiety", "Caffeine worsens anxiety. Heart races uncomfortably."),
    "Sleep Deprivation vs Coffee": ("Sleep Deprivation", "Eventually coffee cannot substitute sleep. Crash is inevitable."),
    "Jitters vs Coffee": ("Jitters", "Too much coffee causes shakes. Hands tremble."),
    "3 PM vs Coffee": ("3 PM", "Afternoon caffeine ruins sleep. Evening coffee is trap."),

    # Banana battles
    "Banana vs Potassium Deficiency": ("Banana", "Bananas restore potassium levels. Electrolyte balance restored."),
    "Banana vs Scale": ("Banana", "Banana is natural measurement unit. Scale for banana established."),
    "Banana vs Monkey": ("Monkey", "Monkeys eat bananas stereotypically. Association is permanent."),
    "Banana vs Radiation": ("Radiation", "Bananas are naturally radioactive. Banana equivalent dose exists."),

    # Banana counters
    "Time vs Banana": ("Time", "Bananas ripen and rot quickly. Time defeats fruit."),
    "Brown Spots vs Banana": ("Brown Spots", "Brown banana is rejected. Aesthetic matters."),
    "Fruit Fly vs Banana": ("Fruit Fly", "Fruit flies swarm ripe bananas. Insects claim fruit."),

    # Burger battles
    "Burger vs Vegetarian": ("Vegetarian", "Vegetarian rejects burger morally. Ethics beat appetite."),
    "Burger vs Napkin": ("Burger", "Burgers are messy. Napkins try but fail."),
    "Burger vs Jaw": ("Burger", "Burger is too tall to bite. Jaw stretches painfully."),
    "Burger vs Bun": ("Burger", "Meat exceeds bun capacity. Structural failure imminent."),

    # Taco battles
    "Taco vs Horizontal Eating": ("Taco", "Tacos must be eaten vertically. Physics demands head tilt."),
    "Taco vs Shell Integrity": ("Taco", "Taco shells break mid-bite. Filling spills catastrophically."),
    "Taco vs White Shirt": ("Taco", "Taco stains white clothing. Food falls unerringly."),
    "Taco vs Tuesday": ("Taco", "Taco Tuesday is sacred. Tradition cannot be broken."),

    # Sushi battles
    "Sushi vs Chopsticks": ("Sushi", "Sushi rolls apart when grabbed. Chopstick skill tested."),
    "Sushi vs Wasabi": ("Wasabi", "Too much wasabi causes sinus pain. Green paste wins."),
    "Sushi vs Soy Sauce": ("Soy Sauce", "Sushi drowns in soy sauce. Sodium content skyrockets."),
    "Sushi vs Freshness": ("Freshness", "Fresh sushi is delicious. Quality is everything."),

    # Sushi counters
    "Time vs Sushi": ("Time", "Raw fish spoils quickly. Freshness window is narrow."),
    "Parasites vs Sushi": ("Parasites", "Improperly prepared sushi contains worms. Biology invades digestion."),

    # Water battles
    "Water vs Fire": ("Water", "Water extinguishes flames. Elemental opposition succeeds."),
    "Water vs Thirst": ("Water", "Water hydrates perfectly. Biological need satisfied."),
    "Water vs Desert": ("Water", "Water enables desert survival. Hydration is life."),
    "Water vs Electronics": ("Water", "Water short-circuits electronics. Liquid beats silicon."),
    "Water vs Drowning": ("Water", "Water fills lungs fatally. Life giver becomes taker."),

    # Water counters
    "Oil vs Water": ("Oil", "Oil and water don't mix. Hydrophobic interaction prevents combination."),
    "Sponge vs Water": ("Sponge", "Sponge absorbs water completely. Porous structure wins."),
    "Evaporation vs Water": ("Evaporation", "Heat turns water to vapor. Phase change occurs."),

    # Energy Drink battles
    "Energy Drink vs Sleep": ("Energy Drink", "Caffeine and sugar defeat sleepiness temporarily. Chemistry overrides biology."),
    "Energy Drink vs Heart": ("Heart", "Energy drinks cause palpitations. Cardiovascular system protests."),
    "Energy Drink vs Teeth": ("Energy Drink", "Acid and sugar erode enamel. Dental damage accumulates."),
    "Energy Drink vs Gamer": ("Gamer", "Energy drinks fuel gaming marathons. Esports run on caffeine."),

    # ============================================================================
    # ABSTRACT CONCEPTS (Love, Time, Space, etc.)
    # ============================================================================

    # Time dominance
    "Time vs Everything": ("Time", "Time erodes all matter and memory. Entropy always increases."),
    "Time vs Mountain": ("Time", "Mountains erode over millennia. Time reduces peaks to plains."),
    "Time vs Civilization": ("Time", "Civilizations rise and fall. Time witnesses all empires crumble."),
    "Time vs Memory": ("Time", "Memories fade as years pass. Time defeats recollection."),
    "Time vs Youth": ("Time", "Youth becomes age inevitably. Time allows no exceptions."),
    "Time vs Beauty": ("Time", "Beauty fades with aging. Time wins through patience."),
    "Time vs Building": ("Time", "Buildings decay and collapse. Time destroys architecture."),
    "Time vs Clock": ("Time", "Clock measures time, doesn't control it. Time marches on regardless."),

    # Time counters
    "Eternity vs Time": ("Eternity", "Eternity transcends time. Time is finite concept within infinity."),
    "Timelessness vs Time": ("Timelessness", "Timeless concepts exist beyond temporal flow. Time cannot touch them."),
    "Moment vs Time": ("Time", "Individual moments compose time's flow. Time contains moments."),

    # Space dominance
    "Space vs Explosion": ("Space", "Space's vacuum contains explosions. No oxygen means no combustion."),
    "Space vs Sound": ("Space", "Sound needs medium to travel. Space's vacuum creates silence."),
    "Space vs Fire": ("Space", "Fire needs oxygen. Space's vacuum extinguishes flames."),
    "Space vs Human": ("Space", "Space is hostile to life. Humans die in seconds."),
    "Space vs Breathing": ("Space", "No atmosphere means no breathing. Suffocation is instant."),

    # Space counters
    "Universe vs Space": ("Universe", "Space exists within universe. Universe contains space."),
    "Matter vs Space": ("Matter", "Matter occupies space. Space is defined by matter's absence."),

    # Gravity dominance
    "Gravity vs Flight": ("Gravity", "All flights must end. Gravity pulls everything down eventually."),
    "Gravity vs Jump": ("Gravity", "Jumps are temporary. Gravity reclaims you immediately."),
    "Gravity vs Orbit": ("Gravity", "Orbit is continuous falling. Gravity controls orbital mechanics."),
    "Gravity vs Escape Velocity": ("Escape Velocity", "Sufficient speed breaks gravitational pull. Physics allows escape."),

    # Entropy dominance
    "Entropy vs Order": ("Entropy", "Disorder increases naturally. Order requires constant energy input."),
    "Entropy vs Organization": ("Entropy", "Organization decays without maintenance. Entropy is inevitable."),
    "Entropy vs Life": ("Entropy", "Life fights entropy temporarily. Death returns atoms to chaos."),
    "Entropy vs Universe": ("Entropy", "Universe trends toward heat death. Entropy wins cosmologically."),

    # Entropy counters
    "Life vs Entropy": ("Life", "Life creates local order despite entropy. Biology defies thermodynamics temporarily."),
    "Negentropy vs Entropy": ("Negentropy", "Negative entropy opposes disorder. Local order increases."),

    # Love battles
    "Love vs Hate": ("Love", "Love conquers hate traditionally. Positivity defeats negativity."),
    "Love vs Logic": ("Love", "Love defies logical explanation. Emotion beats reason."),
    "Love vs Distance": ("Distance", "Long distance kills relationships. Geography defeats romance."),
    "Love vs Time": ("Time", "Time tests love's strength. Years reveal truth."),

    # Love counters
    "Heartbreak vs Love": ("Heartbreak", "Love ends in heartbreak. Pain follows attachment."),
    "Reality vs Love": ("Reality", "Reality kills romance. Practicality defeats idealism."),

    # Hate battles
    "Hate vs Happiness": ("Hate", "Hate destroys happiness. Negativity corrupts joy."),
    "Hate vs Peace": ("Hate", "Hate breeds conflict. Peace cannot survive hatred."),
    "Hate vs Forgiveness": ("Forgiveness", "Forgiveness releases hate. Letting go defeats resentment."),

    # Fear battles
    "Fear vs Courage": ("Courage", "Courage is action despite fear. Bravery defeats paralysis."),
    "Fear vs Rational Thought": ("Fear", "Fear overrides logic. Amygdala hijacks prefrontal cortex."),
    "Fear vs Sleep": ("Fear", "Fear causes insomnia. Anxiety prevents rest."),

    # Mathematics battles
    "Mathematics vs Physics": ("Mathematics", "Physics uses math to describe reality. Math is language of universe."),
    "Mathematics vs Universe": ("Mathematics", "Math describes universal laws. Equations govern cosmos."),
    "Mathematics vs Chaos": ("Mathematics", "Chaos theory mathematically describes disorder. Math encompasses chaos."),
    "Mathematics vs Zero": ("Zero", "Zero is mathematical concept. Math created zero."),

    # Mathematics counters
    "Divide by Zero vs Mathematics": ("Divide by Zero", "Division by zero breaks mathematics. Undefined result crashes system."),
    "Infinity vs Mathematics": ("Infinity", "Infinity breaks normal arithmetic. Math struggles with boundless concepts."),

    # Philosophy battles
    "Philosophy vs Science": ("Science", "Science provides testable answers. Philosophy only asks questions."),
    "Philosophy vs Action": ("Action", "Overthinking prevents action. Philosophy causes paralysis."),
    "Philosophy vs Certainty": ("Philosophy", "Philosophy questions everything. Certainty is illusion."),

    # Art battles
    "Art vs Interpretation": ("Interpretation", "Art means whatever viewer decides. Subjectivity wins."),
    "Art vs Critic": ("Critic", "Critics destroy artists' confidence. Professional judgment hurts."),
    "Art vs Commerce": ("Commerce", "Art must sell to survive. Money controls creativity."),

    # Music battles
    "Music vs Silence": ("Music", "Music fills silence pleasantly. Sound beats emptiness."),
    "Music vs Mood": ("Music", "Music alters emotional state. Rhythm affects brain chemistry."),
    "Music vs Lyrics": ("Lyrics", "Lyrics convey meaning clearly. Words beat instrumentals."),

    # Chaos battles
    "Chaos vs Order": ("Chaos", "Chaos is natural state. Order requires energy to maintain."),
    "Chaos vs Plan": ("Chaos", "No plan survives contact with chaos. Disorder wins."),
    "Chaos vs Control": ("Chaos", "Chaos cannot be controlled. Unpredictability defeats planning."),

    # ============================================================================
    # RANDOM OBJECTS (Rock, Paper, Scissors, Chair, etc.)
    # ============================================================================

    # Classic RPS
    "Rock vs Paper": ("Paper", "Paper covers rock. Classic game theory applies here."),
    "Paper vs Rock": ("Paper", "Paper wraps around rock. Traditional victory holds."),
    "Rock vs Scissors": ("Rock", "Rock crushes scissors. Blunt force wins."),
    "Scissors vs Rock": ("Rock", "Scissors cannot cut rock. Metal dulls on stone."),
    "Paper vs Scissors": ("Scissors", "Scissors cut paper. Sharp edges defeat fiber."),
    "Scissors vs Paper": ("Scissors", "Scissors shred paper easily. Sharp edges win."),

    # Sock battles
    "Sock vs Dryer": ("Dryer", "Dryers steal socks mysteriously. One sock always vanishes."),
    "Sock vs Shoe": ("Shoe", "Shoes contain socks. Footwear hierarchy established."),
    "Sock vs Foot": ("Foot", "Foot wears sock. Anatomy beats fabric."),
    "Wet Socks vs Monday Morning": ("Wet Socks", "Combination creates maximum suffering. Monday alone wasn't miserable enough."),
    "Wet Socks vs Happiness": ("Wet Socks", "Wet socks destroy joy instantly. Dampness defeats morale."),

    # Chair battles
    "Chair vs Standing": ("Chair", "Chair provides comfortable seating. Sitting beats standing."),
    "Chair vs Back Pain": ("Back Pain", "Poor posture causes suffering. Ergonomics matter."),
    "Chair vs Floor": ("Chair", "Chair elevates you above floor. Height advantage gained."),
    "Chair vs Gravity": ("Gravity", "Gravity pulls chair down. Physics wins."),

    # Table battles
    "Table vs Food": ("Table", "Table holds food safely. Surface provides stability."),
    "Table vs Elbow": ("Table", "Don't put elbows on table. Etiquette enforced."),
    "Table vs Leg": ("Table", "Table legs support weight. Four legs beat two."),

    # Bed battles
    "Bed vs Alarm Clock": ("Bed", "Bed's comfort defeats alarm. Snooze button pressed repeatedly."),
    "Bed vs Productivity": ("Bed", "Bed tempts you to sleep. Comfort beats ambition."),
    "Bed vs Morning": ("Bed", "Leaving bed in morning is torture. Warmth wins."),

    # Pillow battles
    "Pillow vs Insomnia": ("Insomnia", "Pillow cannot force sleep. Anxiety wins."),
    "Pillow vs Neck Pain": ("Neck Pain", "Wrong pillow causes pain. Ergonomics matter."),
    "Pillow vs Pillow Fight": ("Pillow Fight", "Pillows weaponized for fun. Violence justified."),

    # Blanket battles
    "Blanket vs Cold": ("Blanket", "Blanket traps body heat. Insulation works perfectly."),
    "Blanket vs Getting Up": ("Blanket", "Blanket cocoon prevents movement. Comfort paralyzes."),
    "Blanket vs Monsters": ("Blanket", "Blanket provides protection from monsters. Childhood logic applies."),

    # Mirror battles
    "Mirror vs Self-Esteem": ("Mirror", "Mirror reveals flaws brutally. Reflection hurts feelings."),
    "Mirror vs Vampire": ("Mirror", "Vampires have no reflection. Mirror exposes undead."),
    "Mirror vs Light": ("Light", "Light reflects off mirror. Mirror needs light."),

    # Lamp battles
    "Lamp vs Darkness": ("Lamp", "Lamp illuminates room. Light defeats shadows."),
    "Lamp vs Moth": ("Lamp", "Moths attracted to lamps fatally. Insects cannot resist."),
    "Lamp vs Power Outage": ("Power Outage", "No electricity means no light. Lamp becomes useless."),

    # ============================================================================
    # MEMES & POP CULTURE (UNO Reverse Card, Shrek, Thanos, etc.)
    # ============================================================================

    # UNO Reverse Card battles
    "UNO Reverse Card vs Insult": ("UNO Reverse Card", "Insult returns to sender. No u energy weaponized."),
    "UNO Reverse Card vs Attack": ("UNO Reverse Card", "Attack bounces back. Meme magic is real."),
    "UNO Reverse Card vs Blame": ("UNO Reverse Card", "Blame reversed completely. Not my fault anymore."),
    "UNO Reverse Card vs Death": ("UNO Reverse Card", "Death reversed. Immortality achieved through meme."),

    # No U battles
    "No U vs Roast": ("No U", "Ultimate comeback activated. Roast reflected."),
    "No U vs Argument": ("No U", "Argument ends instantly. No u is checkmate."),
    "No U vs Logic": ("No U", "Logic irrelevant. Meme power wins."),

    # Shrek battles
    "Shrek vs Donkey": ("Shrek", "Shrek tolerates Donkey barely. Ogre patience tested."),
    "Shrek vs Farquaad": ("Shrek", "Shrek defeated Farquaad. Movie proves this."),
    "Shrek vs Beauty Standards": ("Shrek", "Shrek redefines beauty. Ogres are beautiful."),
    "Shrek vs Swamp": ("Swamp", "Swamp is Shrek's home. Environment contains ogre."),

    # Thanos battles
    "Thanos vs Half the Universe": ("Thanos", "Snap erases half of life. Perfectly balanced."),
    "Thanos vs Avengers": ("Thanos", "Thanos won initially. Infinity stones dominate."),
    "Thanos vs Iron Man": ("Iron Man", "Iron Man reversed snap. Self-sacrifice wins."),
    "Thanos vs Balance": ("Balance", "Thanos seeks balance. Concept drives villain."),

    # John Cena battles
    "John Cena vs Visibility": ("Visibility", "You can't see John Cena. Invisibility is his power."),
    "John Cena vs Wrestling": ("John Cena", "John Cena dominates WWE. Championship record speaks."),
    "John Cena vs Meme": ("Meme", "Cena became meme. Internet immortality achieved."),

    # Doge battles
    "Doge vs Cryptocurrency": ("Doge", "Dogecoin proves memes have value. Much wow economics."),
    "Doge vs Grammar": ("Doge", "Doge ignores grammar rules. Such rebel. Very freedom."),
    "Doge vs Seriousness": ("Doge", "Doge makes everything silly. Humor defeats gravity."),

    # Pepe battles
    "Pepe vs Sadness": ("Pepe", "Pepe embodies sadness. Feels bad man wins."),
    "Pepe vs Rarity": ("Pepe", "Rare pepes have value. Scarcity drives meme economy."),
    "Pepe vs Controversy": ("Controversy", "Pepe became controversial. Context defeats intent."),

    # Chad battles
    "Chad vs Virgin": ("Chad", "Chad dominates virgin. Meme hierarchy established."),
    "Chad vs Insecurity": ("Chad", "Chad has no insecurities. Confidence absolute."),
    "Chad vs Gym": ("Gym", "Gym creates Chads. Training builds muscle."),

    # Sigma Male battles
    "Sigma Male vs Alpha Male": ("Sigma Male", "Sigma operates outside hierarchy. Lone wolf wins."),
    "Sigma Male vs Society": ("Sigma Male", "Sigma rejects social norms. Independence chosen."),
    "Sigma Male vs Grindset": ("Grindset", "Grindset defines sigma. Hustle never stops."),

    # Based God battles
    "Based God vs Curse": ("Based God", "Based God curses disbelievers. Basketball players fear him."),
    "Based God vs Thank You": ("Based God", "Thank you Based God. Gratitude required."),

    # Ligma/Joe Mama/Deez Nuts battles
    "Ligma vs Awareness": ("Ligma", "What's ligma? Gotcha. Meme trap successful."),
    "Joe Mama vs Respect": ("Joe Mama", "Joe mama joke deployed. Disrespect achieved."),
    "Deez Nuts vs Dignity": ("Deez Nuts", "Got eem. Dignity destroyed."),

    # ============================================================================
    # COMPLETELY RANDOM (Existential Dread, Monday Morning, etc.)
    # ============================================================================

    # Existential Dread battles
    "Existential Dread vs Happiness": ("Existential Dread", "Dread crushes joy. Meaninglessness wins."),
    "Existential Dread vs 3 AM": ("Existential Dread", "3 AM amplifies existential thoughts. Dark hours enable philosophy."),
    "Existential Dread vs Purpose": ("Purpose", "Finding purpose defeats dread. Meaning provides direction."),
    "Existential Dread vs Therapy": ("Therapy", "Therapy addresses dread. Professional help works."),

    # Monday Morning battles
    "Monday Morning vs Weekend": ("Monday Morning", "Monday ends weekend cruelly. Work resumes."),
    "Monday Morning vs Motivation": ("Monday Morning", "Mondays kill motivation. Weekly reset depresses."),
    "Monday Morning vs Coffee": ("Coffee", "Coffee makes Mondays tolerable. Caffeine is necessity."),
    "Monday Morning vs Alarm": ("Monday Morning", "Monday alarms are torture. Weekend ended."),

    # Traffic Jam battles
    "Traffic Jam vs Productivity": ("Traffic Jam", "Traffic wastes hours daily. Commute steals life."),
    "Traffic Jam vs Patience": ("Traffic Jam", "Traffic tests patience severely. Road rage emerges."),
    "Traffic Jam vs Podcast": ("Podcast", "Podcasts make traffic bearable. Entertainment passes time."),

    # Lag Spike battles
    "Lag Spike vs Gaming": ("Lag Spike", "Lag ruins competitive games. Network latency destroys skill."),
    "Lag Spike vs Clutch Moment": ("Lag Spike", "Lag strikes during crucial plays. Victory stolen."),
    "Lag Spike vs Ping": ("Lag Spike", "High ping equals lag. Network delay measured."),

    # Loading Screen battles
    "Loading Screen vs Patience": ("Loading Screen", "Loading screens test patience. Progress bar lies."),
    "Loading Screen vs Time": ("Loading Screen", "Loading wastes time. Optimization needed."),
    "Loading Screen vs SSD": ("SSD", "SSD eliminates loading screens. Speed beats loading."),

    # 404 Error battles
    "404 Error vs Website": ("404 Error", "Page not found. Website broken."),
    "404 Error vs User": ("404 Error", "User frustrated by error. Navigation failed."),
    "404 Error vs Link": ("404 Error", "Link broken. Error defeats connection."),

    # Blue Screen battles
    "Blue Screen vs Progress": ("Blue Screen", "Unsaved work lost. Blue screen destroys hours."),
    "Blue Screen vs Windows": ("Blue Screen", "Windows crashes spectacularly. Operating system failed."),
    "Blue Screen vs Deadline": ("Blue Screen", "Blue screen before deadline. Maximum panic achieved."),

    # Low Battery battles
    "Low Battery vs Important Call": ("Low Battery", "Phone dies during call. Battery timing impeccable."),
    "Low Battery vs GPS": ("Low Battery", "Battery dies while lost. Navigation failed."),
    "Low Battery vs Charger": ("Charger", "Charger resurrects device. Power restored."),

    # Stepping on LEGO battles
    "Stepping on LEGO vs Pain": ("Stepping on LEGO", "LEGO is ultimate pain. Foot agony maximized."),
    "Stepping on LEGO vs Bare Feet": ("Stepping on LEGO", "Bare feet plus LEGO equals torture. Sharp plastic wins."),
    "Stepping on LEGO vs Landmine": ("Stepping on LEGO", "LEGO hurts more than landmine. Child's toy weaponized."),

    # Brain Freeze battles
    "Brain Freeze vs Ice Cream": ("Ice Cream", "Ice cream worth the pain. Delicious justifies suffering."),
    "Brain Freeze vs Speed": ("Brain Freeze", "Eating too fast causes freeze. Pace matters."),

    # Stubbed Toe battles
    "Stubbed Toe vs Furniture": ("Furniture", "Furniture attacks toes. Corner ambush successful."),
    "Stubbed Toe vs Pain": ("Stubbed Toe", "Toe stubbing causes disproportionate pain. Nerve endings suffer."),

    # Paper Cut battles
    "Paper Cut vs Pain Scale": ("Paper Cut", "Paper cuts hurt more than expected. Thin slice deep."),
    "Paper Cut vs Paper": ("Paper", "Paper weaponized. Sharp edge cuts skin."),

    # Hiccups battles
    "Hiccups vs Silence": ("Hiccups", "Hiccups interrupt everything. Diaphragm rebels."),
    "Hiccups vs Water": ("Water", "Drinking water stops hiccups sometimes. Hydration helps."),
    "Hiccups vs Scare": ("Scare", "Sudden scare stops hiccups. Adrenaline resets diaphragm."),

    # Cringe battles
    "Cringe vs Memory": ("Cringe", "Cringe memories haunt forever. Past embarrassment persists."),
    "Cringe vs Social Media": ("Social Media", "Social media preserves cringe. Internet never forgets."),
    "Cringe vs 3 AM": ("Cringe", "3 AM replays cringe moments. Sleep impossible."),

    # ============================================================================
    # ADDITIONAL CROSS-CATEGORY MATCHUPS
    # ============================================================================

    # Tech vs Food
    "Toaster vs Bread": ("Toaster", "Toaster transforms bread. Heat creates toast."),
    "Microwave vs Pizza": ("Microwave", "Microwave reheats pizza poorly. Soggy crust results."),
    "Refrigerator vs Milk": ("Refrigerator", "Refrigerator preserves milk. Cold prevents spoiling."),
    "Blender vs Banana": ("Blender", "Blender liquefies banana. Smoothie created."),

    # Animals vs Food
    "Dog vs Chocolate": ("Chocolate", "Chocolate poisons dogs. Theobromine is toxic."),
    "Cat vs Tuna": ("Tuna", "Cats love tuna. Fish attracts felines."),
    "Bear vs Honey": ("Bear", "Bears raid hives for honey. Sweet tooth drives theft."),
    "Ant vs Crumb": ("Ant", "Ants carry crumbs home. Teamwork transports food."),

    # Memes vs Reality
    "Doge vs Real Dog": ("Real Dog", "Real dogs don't speak broken English. Biology beats meme."),
    "Pepe vs Real Frog": ("Real Frog", "Real frogs don't feel sad. Amphibians lack emotion."),
    "Chad vs Real Person": ("Real Person", "Real people have flaws. Perfection is myth."),

    # Weather vs Tech
    "Rain vs Smartphone": ("Rain", "Water damage destroys phones. Rain wins."),
    "Lightning vs Power Grid": ("Lightning", "Lightning causes blackouts. Electricity meets electricity."),
    "Snow vs Internet": ("Snow", "Snow damages infrastructure. Connectivity lost."),

    # Concepts vs Objects
    "Time vs Watch": ("Time", "Watches measure time, don't create it. Time exists independently."),
    "Love vs Ring": ("Ring", "Ring symbolizes love but isn't love. Symbol differs from concept."),
    "Fear vs Boogeyman": ("Fear", "Fear creates boogeyman. Emotion manifests monster."),
    "Anger vs Punching Bag": ("Punching Bag", "Punching bag absorbs anger. Outlet prevents damage."),

    # Size Mismatches
    "Ant vs Elephant": ("Elephant", "Elephant can step on millions of ants. Size dominates."),
    "Mouse vs Whale": ("Whale", "Whale is thousands of times larger. Scale matters."),
    "Pebble vs Mountain": ("Mountain", "Mountain contains billions of pebbles. Mass wins."),
    "Raindrop vs Ocean": ("Ocean", "Ocean contains quintillions of raindrops. Volume dominates."),

    # Ironic Reversals
    "Toothpick vs Tree": ("Tree", "Tree becomes millions of toothpicks. Source beats product."),
    "Pixel vs Screen": ("Screen", "Screen contains millions of pixels. Whole beats part."),
    "Note vs Symphony": ("Symphony", "Symphony combines countless notes. Composition transcends component."),
    "Word vs Dictionary": ("Dictionary", "Dictionary contains all words. Collection beats individual."),

    # Meta Battles
    "Game vs Player": ("Player", "Player controls game. Human agency wins."),
    "Bot vs Creator": ("Creator", "Creator programmed bot. Source has authority."),
    "Simulation vs Reality": ("Reality", "Reality contains simulations. Base level wins."),
    "Dream vs Dreamer": ("Dreamer", "Dreamer creates dreams. Consciousness beats imagination."),

    # Practical Counters
    "Umbrella vs Rain": ("Umbrella", "Umbrella deflects rain. Tool beats weather."),
    "Sunglasses vs Sun": ("Sunglasses", "Sunglasses filter sunlight. Protection works."),
    "Helmet vs Falling Object": ("Helmet", "Helmet protects head. Safety equipment saves."),
    "Mask vs Virus": ("Mask", "Mask filters viral particles. Barrier prevents infection."),

    # Energy vs Matter
    "Electricity vs Water": ("Water", "Water conducts electricity fatally. Liquid beats current."),
    "Heat vs Ice": ("Heat", "Heat melts ice. Thermal energy wins."),
    "Cold vs Fire": ("Fire", "Fire generates heat. Combustion beats cold."),
    "Magnetism vs Iron": ("Magnetism", "Magnetism attracts iron. Force manipulates matter."),

    # Human Needs
    "Hunger vs Food": ("Food", "Food satisfies hunger. Nutrition defeats appetite."),
    "Thirst vs Water": ("Water", "Water quenches thirst. Hydration essential."),
    "Fatigue vs Sleep": ("Sleep", "Sleep cures fatigue. Rest restores energy."),
    "Pain vs Medicine": ("Medicine", "Medicine relieves pain. Pharmacology works."),

    # Status Effects
    "Poison vs Antidote": ("Antidote", "Antidote neutralizes poison. Cure beats toxin."),
    "Disease vs Vaccine": ("Vaccine", "Vaccine prevents disease. Immunization works."),
    "Infection vs Antibiotic": ("Antibiotic", "Antibiotic kills bacteria. Medicine defeats infection."),
    "Wound vs Bandage": ("Bandage", "Bandage stops bleeding. First aid helps."),

    # Final Random Matchups
    "Eraser vs Pencil": ("Eraser", "Eraser removes pencil marks. Correction beats writing."),
    "Stapler vs Paper": ("Stapler", "Stapler binds papers together. Tool organizes."),
    "Thumbtack vs Cork Board": ("Thumbtack", "Thumbtack pins to board. Sharp point penetrates."),
    "Butter Knife vs Butter": ("Butter Knife", "Butter knife spreads butter. Tool manipulates food."),
    "Fork vs Spaghetti": ("Fork", "Fork twirls spaghetti. Utensil conquers pasta."),
    "Grape vs Wine": ("Wine", "Wine is fermented grapes. Processing transforms fruit."),
    "Orange vs Juice": ("Orange", "Orange becomes juice. Source beats product."),
    "Egg vs Chicken": ("Chicken", "Chicken lays egg. Biology solves riddle."),
    "Bacon vs Pig": ("Pig", "Pig creates bacon. Animal beats product."),
    "Cheese vs Mouse": ("Mouse", "Mouse loves cheese. Stereotypical attraction real."),
}
