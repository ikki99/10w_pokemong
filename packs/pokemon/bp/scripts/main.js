// Pokémon 怪物包 — 招式 / 屬性克制 / 精靈球捕捉 / 圖鑑 / 夥伴跟隨
// 由 tools/gen_pokemon.py 複製到 bp/scripts/main.js
import { world, system, ItemStack } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import "./worlds.js";  // 主題世界：傳送廣場 + 區域生成

const TAG = "[Poke]";
const VERSION = "5.0.33";
console.log(`${TAG} module loaded (v${VERSION})`);

// ============================================================ 屬性

const POKE_TYPE = {
  "poke:pikachu": "electric",
  "poke:eevee": "normal",
  "poke:bulbasaur": "grass",
  "poke:charmander": "fire",
  "poke:squirtle": "water",
  "poke:jigglypuff": "fairy",
  "poke:meowth": "normal",
  "poke:gengar": "ghost",
  "poke:snorlax": "normal",
  "poke:dragonite": "dragon",
  "poke:charizard": "fire",
  "poke:mewtwo": "psychic",
  // ---- 第二批 12 隻 ----
  "poke:psyduck": "water",
  "poke:gyarados": "water",
  "poke:lapras": "water",
  "poke:machamp": "fighting",
  "poke:alakazam": "psychic",
  "poke:onix": "rock",
  "poke:lucario": "fighting",
  "poke:gardevoir": "psychic",
  "poke:greninja": "water",
  "poke:mimikyu": "ghost",
  "poke:sylveon": "fairy",
  "poke:garchomp": "dragon",
  // ---- 第三批：傳說 ----
  "poke:lugia": "psychic",
  "poke:hooh": "fire",
  "poke:rayquaza": "dragon",
  "poke:latias": "dragon",
  "poke:latios": "dragon",
  "poke:regigigas": "normal",
  "poke:mew": "psychic",
  "poke:xerneas": "fairy",
  "poke:eternatus": "poison",
  "poke:dialga": "steel",
  "poke:palkia": "water",
  "poke:giratina": "ghost",
  "poke:arceus": "normal",
  "poke:articuno": "ice",
  "poke:zapdos": "electric",
  "poke:moltres": "fire",
  "poke:aerodactyl": "rock",
  "poke:regirock": "rock",
  "poke:regice": "ice",
  "poke:registeel": "steel",
  "poke:regieleki": "electric",
  "poke:regidrago": "dragon",
  "poke:zarude": "grass",
  "poke:tyranitar": "rock",
  "poke:salamence": "dragon",
  "poke:metagross": "steel",
  "poke:hydreigon": "dark",
  "poke:goodra": "dragon",
  "poke:kommoo": "dragon",
  "poke:dragapult": "dragon",
  "poke:duraludon": "steel",
  "poke:baxcalibur": "dragon",
  "poke:garganacl": "rock",
};

const TOTAL_SPECIES = Object.keys(POKE_TYPE).length;

// ---- 異色（shiny）與本體共用屬性/招式/中文名，只是實體 id 與貼圖不同 ----
const SHINY_SUFFIX = "_shiny";
const isShinyId = (id) => typeof id === "string" && id.endsWith(SHINY_SUFFIX);
const baseOf = (id) => (isShinyId(id) ? id.slice(0, -SHINY_SUFFIX.length) : id);

function mirrorShiny(target, labelFn) {
  for (const id of Object.keys(target)) {
    if (isShinyId(id)) continue;
    target[`${id}${SHINY_SUFFIX}`] = labelFn ? undefined : target[id];
  }
}

for (const id of Object.keys(POKE_TYPE)) {
  if (!isShinyId(id)) POKE_TYPE[`${id}${SHINY_SUFFIX}`] = POKE_TYPE[id];
}

// 圖鑑只列基礎型（異色用 ✦ 標記）—— 必須放在 POKE_TYPE 鏡像之後
const BASE_IDS = Object.keys(POKE_TYPE).filter((id) => !isShinyId(id));

const TYPE_CHART = {
  electric: { water: 2, grass: 0.5, dragon: 0.5, ground: 0 },
  normal: { ghost: 0, rock: 0.5, steel: 0.5 },
  grass: { water: 2, ground: 2, rock: 2, fire: 0.5, grass: 0.5, dragon: 0.5, steel: 0.5 },
  fire: { grass: 2, ice: 2, steel: 2, water: 0.5, fire: 0.5, dragon: 0.5, rock: 0.5 },
  water: { fire: 2, ground: 2, rock: 2, water: 0.5, grass: 0.5, dragon: 0.5 },
  fairy: { dragon: 2, fighting: 2, dark: 2, fire: 0.5, steel: 0.5 },
  ghost: { psychic: 2, ghost: 2, normal: 0, dark: 0.5 },
  dragon: { dragon: 2, fairy: 0.5, steel: 0.5 },
  psychic: { fighting: 2, ghost: 0.5, psychic: 0.5, dark: 0.5, steel: 0.5 },
  fighting: { normal: 2, rock: 2, steel: 2, ice: 2, dark: 2, psychic: 0.5, fairy: 0.5, ghost: 0 },
  rock: { fire: 2, ice: 2, fighting: 0.5, ground: 0.5, steel: 0.5 },
  steel: { fairy: 2, rock: 2, ice: 2, fire: 0.5, water: 0.5, steel: 0.5 },
  dark: { psychic: 2, ghost: 2, fighting: 0.5, dark: 0.5, fairy: 0.5 },
  ice: { dragon: 2, grass: 2, ground: 2, water: 0.5, ice: 0.5, fire: 0.5 },
  ground: { fire: 2, electric: 2, rock: 2, grass: 0.5 },
};

const TYPE_ZH = {
  electric: "電", normal: "一般", grass: "草", fire: "火", water: "水",
  fairy: "妖精", ghost: "幽靈", dragon: "龍", psychic: "超能力", ground: "地面",
  fighting: "格鬥", rock: "岩石", steel: "鋼", dark: "邪惡", ice: "冰",
};

const NAME_ZH = {
  "poke:pikachu": "皮卡丘",
  "poke:eevee": "伊布",
  "poke:bulbasaur": "妙蛙種子",
  "poke:charmander": "小火龍",
  "poke:squirtle": "傑尼龜",
  "poke:jigglypuff": "胖丁",
  "poke:meowth": "喵喵",
  "poke:gengar": "耿鬼",
  "poke:snorlax": "卡比獸",
  "poke:dragonite": "快龍",
  "poke:charizard": "噴火龍",
  "poke:mewtwo": "超夢",
  "poke:psyduck": "可達鴨",
  "poke:gyarados": "暴鯉龍",
  "poke:lapras": "拉普拉斯",
  "poke:machamp": "怪力",
  "poke:alakazam": "胡地",
  "poke:onix": "大岩蛇",
  "poke:lucario": "路卡利歐",
  "poke:gardevoir": "沙奈朵",
  "poke:greninja": "甲賀忍蛙",
  "poke:mimikyu": "謎擬Q",
  "poke:sylveon": "仙子伊布",
  "poke:garchomp": "烈咬陸鯊",
  // ---- 傳說 ----
  "poke:lugia": "洛奇亞",
  "poke:hooh": "鳳王",
  "poke:rayquaza": "烈空坐",
  "poke:latias": "拉帝亞斯",
  "poke:latios": "拉帝歐斯",
  "poke:regigigas": "雷吉奇卡斯",
  "poke:mew": "夢幻",
  "poke:xerneas": "哲爾尼亞斯",
  "poke:eternatus": "無極汰那",
  "poke:dialga": "帝牙盧卡",
  "poke:palkia": "帕路奇亞",
  "poke:giratina": "騎拉帝納",
  "poke:arceus": "阿爾宙斯",
  "poke:articuno": "急凍鳥",
  "poke:zapdos": "閃電鳥",
  "poke:moltres": "火焰鳥",
  "poke:aerodactyl": "化石翼龍",
  "poke:regirock": "雷吉洛克",
  "poke:regice": "雷吉艾斯",
  "poke:registeel": "雷吉斯奇魯",
  "poke:regieleki": "雷吉艾勒奇",
  "poke:regidrago": "雷吉鐸拉戈",
  "poke:zarude": "薩戮德",
  "poke:tyranitar": "班基拉斯",
  "poke:salamence": "暴飛龍",
  "poke:metagross": "巨金怪",
  "poke:hydreigon": "三首惡龍",
  "poke:goodra": "黏美龍",
  "poke:kommoo": "杖尾鱗甲龍",
  "poke:dragapult": "多龍巴魯托",
  "poke:duraludon": "鋁鋼龍",
  "poke:baxcalibur": "戟脊龍",
  "poke:garganacl": "鹽石巨靈",
};

for (const id of Object.keys(NAME_ZH)) {
  if (!isShinyId(id)) NAME_ZH[`${id}${SHINY_SUFFIX}`] = `${NAME_ZH[id]}（異色）`;
}

function typeMultiplier(atkType, defEntity) {
  const defType = POKE_TYPE[defEntity?.typeId];
  if (!defType) return 1;
  return TYPE_CHART[atkType]?.[defType] ?? 1;
}

function hit(atkEntity, target, base, type, cause = "entityAttack") {
  const mult = typeMultiplier(type, target);
  if (mult === 0) {
    try { target.dimension.spawnParticle("minecraft:villager_happy", target.location); } catch (e) {}
    console.log(`${TAG} ${TYPE_ZH[type] ?? type}系對 ${target.typeId} 無效`);
    return 0;
  }
  const dmg = base * mult;
  try { target.applyDamage(dmg, { cause, damagingEntity: atkEntity }); } catch (e) {}
  if (mult > 1) console.log(`${TAG} 效果絕佳 ${TYPE_ZH[type] ?? type} x${mult}`);
  else if (mult < 1) console.log(`${TAG} 效果不理想 x${mult}`);
  return dmg;
}

// ============================================================ 冷卻 / 特效

const COOLDOWN_TICKS = 80;
const lastMove = new Map();

function offCooldown(entity) {
  const now = system.currentTick;
  const prev = lastMove.get(entity.id) ?? -9999;
  if (now - prev < COOLDOWN_TICKS) return false;
  lastMove.set(entity.id, now);
  return true;
}

function fx(dim, loc, particle, sound, pitch = 1) {
  try { dim.spawnParticle(particle, loc); } catch (e) {}
  if (sound) {
    try { dim.playSound(sound, loc, { volume: 1, pitch }); } catch (e) {}
  }
}

// applyKnockback 在新版是 (VectorXZ, 垂直力)，舊版是 (x, z, 水平, 垂直)，兩種都試
function applyKb(entity, dx, dz, horizontal, vertical = 0) {
  try {
    entity.applyKnockback({ x: dx, z: dz }, vertical);
    return true;
  } catch (e) {}
  try {
    entity.applyKnockback(dx, dz, horizontal, vertical);
    return true;
  } catch (e) {}
  return false;
}

function knock(attacker, target, strength, vertical) {
  try {
    const dx = target.location.x - attacker.location.x;
    const dz = target.location.z - attacker.location.z;
    const len = Math.max(0.1, Math.hypot(dx, dz));
    applyKb(target, (dx / len) * strength, (dz / len) * strength, strength, vertical);
  } catch (e) {}
}

// ============================================================ 招式

const MOVES = {
  thunder(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_flame_particle", "random.explode", 1.6);
    hit(self, t, 4, "electric");
    try { t.addEffect("slowness", 60, { amplifier: 1 }); } catch (e) {}
    return "皮卡丘：十萬伏特！";
  },
  ember(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_flame_particle", "mob.blaze.breathe", 1.4);
    t.setOnFire(5, true);
    hit(self, t, 3, "fire", "fire");
    return "小火龍：火花！";
  },
  flamethrower(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_flame_particle", "mob.enderdragon.flap", 1.1);
    t.setOnFire(8, true);
    hit(self, t, 6, "fire", "fire");
    return "噴火龍：噴射火焰！";
  },
  watergun(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_smoke_particle", "random.splash", 1.3);
    hit(self, t, 3, "water");
    knock(self, t, 1.6, 0.4);
    return "傑尼龜：水槍！";
  },
  vinesnare(self, t) {
    fx(t.dimension, t.location, "minecraft:villager_happy", "mob.shulker.shoot", 0.7);
    hit(self, t, 2, "grass");
    try { t.addEffect("slowness", 100, { amplifier: 3 }); } catch (e) {}
    try { t.addEffect("poison", 80, { amplifier: 0 }); } catch (e) {}
    return "妙蛙種子：藤鞭纏繞！";
  },
  swift(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.arrow.hit_player", 1.5);
    hit(self, t, 2, "normal");
    try { self.addEffect("speed", 200, { amplifier: 1 }); } catch (e) {}
    return "伊布：電光一閃！";
  },
  payday(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "random.orb", 1.2);
    hit(self, t, 3, "normal");
    return "喵喵：聚寶功！";
  },
  sing(self) {
    const dim = self.dimension;
    fx(dim, self.location, "minecraft:heart_particle", "mob.ghast.moan", 1.8);
    let n = 0;
    for (const p of dim.getPlayers({ location: self.location, maxDistance: 10 })) {
      try {
        p.addEffect("blindness", 120, { amplifier: 0 });
        p.addEffect("slowness", 120, { amplifier: 2 });
        p.sendMessage("§d胖丁：搖籃曲…你開始想睡了");
        n++;
      } catch (e) {}
    }
    return n ? `胖丁：搖籃曲！${n} 人陷入睡意` : "胖丁：搖籃曲！";
  },
  shadow(self, t) {
    const dim = self.dimension;
    fx(dim, t.location, "minecraft:basic_smoke_particle", "mob.endermen.portal", 0.9);
    try { self.teleport({ x: t.location.x + 1.2, y: t.location.y, z: t.location.z + 1.2 }, { dimension: dim }); } catch (e) {}
    try { t.addEffect("darkness", 100, { amplifier: 0 }); } catch (e) {}
    hit(self, t, 4, "ghost", "magic");
    return "耿鬼：暗影潛襲！";
  },
  bodyslam(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_smoke_particle", "mob.iron_golem.step", 0.6);
    hit(self, t, 5, "normal");
    knock(self, t, 3, 0.8);
    return "卡比獸：重磅衝撞！";
  },
  dragontail(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.enderdragon.growl", 1.3);
    hit(self, t, 6, "dragon");
    knock(self, t, 2.5, 0.9);
    return "快龍：龍尾！";
  },
  confusion(self, t) {
    fx(t.dimension, t.location, "minecraft:villager_happy", "mob.endermen.portal", 1.4);
    hit(self, t, 3, "psychic", "magic");
    try { t.addEffect("nausea", 120, { amplifier: 0 }); } catch (e) {}
    return "可達鴨：念力！";
  },
  hydropump(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_smoke_particle", "random.splash", 0.7);
    hit(self, t, 8, "water");
    knock(self, t, 3.2, 0.6);
    return "暴鯉龍：水炮！";
  },
  icebeam(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_snowball_particle", "random.glass", 1.2);
    hit(self, t, 5, "ice");
    try { t.addEffect("slowness", 120, { amplifier: 3 }); } catch (e) {}
    return "拉普拉斯：冰凍光束！";
  },
  shuriken(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.arrow.hit", 1.6);
    hit(self, t, 3, "water");
    hit(self, t, 2, "dark");
    try { self.addEffect("speed", 160, { amplifier: 2 }); } catch (e) {}
    return "甲賀忍蛙：飛水手裡劍！";
  },
  dynamicpunch(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.irongolem.attack", 0.8);
    hit(self, t, 7, "fighting");
    knock(self, t, 4.0, 1.0);
    try { t.addEffect("nausea", 140, { amplifier: 1 }); } catch (e) {}
    return "怪力：爆裂拳！";
  },
  psyshock(self, t) {
    fx(t.dimension, t.location, "minecraft:villager_happy", "mob.shulker.teleport", 0.9);
    hit(self, t, 6, "psychic", "magic");
    try { t.addEffect("levitation", 30, { amplifier: 2 }); } catch (e) {}
    return "胡地：精神衝擊！";
  },
  rockthrow(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_smoke_particle", "dig.stone", 0.8);
    hit(self, t, 4, "rock");
    knock(self, t, 2.0, 0.7);
    return "大岩蛇：落石！";
  },
  aurasphere(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.wither.shoot", 1.3);
    hit(self, t, 6, "fighting", "magic");
    return "路卡利歐：波導彈！";
  },
  moonblast(self, t) {
    fx(t.dimension, t.location, "minecraft:heart_particle", "mob.enderdragon.growl", 1.7);
    hit(self, t, 6, "fairy", "magic");
    try { t.addEffect("weakness", 140, { amplifier: 1 }); } catch (e) {}
    return "沙奈朵：月亮之力！";
  },
  shadowclaw(self, t) {
    fx(t.dimension, t.location, "minecraft:basic_smoke_particle", "mob.endermen.stare", 1.1);
    hit(self, t, 5, "ghost");
    try { t.addEffect("darkness", 80, { amplifier: 0 }); } catch (e) {}
    return "謎擬Q：暗影爪！";
  },
  fairywind(self, t) {
    fx(t.dimension, t.location, "minecraft:heart_particle", "mob.ghast.scream", 2.0);
    hit(self, t, 4, "fairy", "magic");
    try {
      const hp = self.getComponent("minecraft:health");
      hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 3));
    } catch (e) {}
    return "仙子伊布：妖精之風！";
  },
  dragonclaw(self, t) {
    fx(t.dimension, t.location, "minecraft:critical_hit_emitter", "mob.enderdragon.growl", 1.0);
    hit(self, t, 7, "dragon");
    knock(self, t, 2.2, 0.5);
    return "烈咬陸鯊：龍爪！";
  },
  psychic(self, t) {
    fx(t.dimension, t.location, "minecraft:villager_happy", "mob.shulker.teleport", 0.6);
    hit(self, t, 7, "psychic", "magic");
    try { t.addEffect("levitation", 40, { amplifier: 3 }); } catch (e) {}
    try { t.addEffect("weakness", 120, { amplifier: 2 }); } catch (e) {}
    return "超夢：幻象光線！";
  },
};

const ABILITY = {
  "poke:pikachu": "thunder",
  "poke:eevee": "swift",
  "poke:bulbasaur": "vinesnare",
  "poke:charmander": "ember",
  "poke:squirtle": "watergun",
  "poke:jigglypuff": "sing",
  "poke:meowth": "payday",
  "poke:gengar": "shadow",
  "poke:snorlax": "bodyslam",
  "poke:dragonite": "dragontail",
  "poke:charizard": "flamethrower",
  "poke:mewtwo": "psychic",
  "poke:psyduck": "confusion",
  "poke:gyarados": "hydropump",
  "poke:lapras": "icebeam",
  "poke:machamp": "dynamicpunch",
  "poke:alakazam": "psyshock",
  "poke:onix": "rockthrow",
  "poke:lucario": "aurasphere",
  "poke:gardevoir": "moonblast",
  "poke:greninja": "shuriken",
  "poke:mimikyu": "shadowclaw",
  "poke:sylveon": "fairywind",
  "poke:garchomp": "dragonclaw",
};


for (const id of Object.keys(ABILITY)) {
  if (!isShinyId(id)) ABILITY[`${id}${SHINY_SUFFIX}`] = ABILITY[id];
}

function runMove(self, target) {
  const moveId = ABILITY[self.typeId];
  if (!moveId || !offCooldown(self)) return;
  const fn = MOVES[moveId];
  if (!fn) return;
  try {
    const msg = fn(self, target);
    if (msg) console.log(`${TAG} ${msg}`);
  } catch (e) {
    console.log(`${TAG} move error ${moveId}: ${e}`);
  }
}

// 玩家打寶可夢 -> 反擊
world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const defender = ev.hitEntity;
    const attacker = ev.damagingEntity;
    if (!defender || !ABILITY[defender.typeId]) return;
    if (!attacker || attacker.typeId !== "minecraft:player") return;
    runMove(defender, attacker);
  } catch (e) {}
});

// ============================================================ 圖鑑紀錄

const DEX_KEY = "poke:dex";

function readDex() {
  try {
    return JSON.parse(world.getDynamicProperty(DEX_KEY) ?? "{}");
  } catch (e) {
    return {};
  }
}

function writeDex(d) {
  try { world.setDynamicProperty(DEX_KEY, JSON.stringify(d)); } catch (e) {}
}

function addToDex(typeId) {
  const d = readDex();
  d[typeId] = (d[typeId] ?? 0) + 1;
  writeDex(d);
  return d[typeId];
}

// ============================================================ 精靈球

const BALL_ITEM = "poke:pokeball";
const DEX_ITEM = "poke:pokedex";

// 各種球的加成（1.0 以上 = 必中）
const BALL_BONUS = {
  "poke:pokeball": 0, "poke:greatball": 0.15, "poke:ultraball": 0.30, "poke:masterball": 1.0,
  "poke:dive_ball": 0.20, "poke:dusk_ball": 0.20, "poke:timer_ball": 0.18, "poke:quick_ball": 0.25,
  "poke:repeat_ball": 0.15, "poke:net_ball": 0.15, "poke:nest_ball": 0.15, "poke:luxury_ball": 0.12,
  "poke:heal_ball": 0.12, "poke:friend_ball": 0.12, "poke:love_ball": 0.15, "poke:moon_ball": 0.15,
  "poke:fast_ball": 0.15, "poke:heavy_ball": 0.15, "poke:level_ball": 0.15, "poke:lure_ball": 0.15,
  "poke:premier_ball": 0.05, "poke:safari_ball": 0.20, "poke:dream_ball": 0.25, "poke:beast_ball": 0.40,
};
const BALL_NAMES = {
  "poke:pokeball": "精靈球", "poke:greatball": "高級球", "poke:ultraball": "超級球", "poke:masterball": "大師球",
  "poke:dive_ball": "潛水球", "poke:dusk_ball": "黑暗球", "poke:timer_ball": "計時球", "poke:quick_ball": "先機球",
  "poke:repeat_ball": "重複球", "poke:net_ball": "捕蟲球", "poke:nest_ball": "巢穴球", "poke:luxury_ball": "奢華球",
  "poke:heal_ball": "治癒球", "poke:friend_ball": "友友球", "poke:love_ball": "甜蜜球", "poke:moon_ball": "月亮球",
  "poke:fast_ball": "速度球", "poke:heavy_ball": "沉重球", "poke:level_ball": "等級球", "poke:lure_ball": "誘餌球",
  "poke:premier_ball": "紀念球", "poke:safari_ball": "狩獵球", "poke:dream_ball": "夢境球", "poke:beast_ball": "究極球",
};
const isBall = (typeId) => Object.prototype.hasOwnProperty.call(BALL_BONUS, typeId);

function nearestPoke(player, radius = 12) {
  let best = null;
  let bestD = Infinity;
  try {
    for (const e of player.dimension.getEntities({ location: player.location, maxDistance: radius })) {
      if (!POKE_TYPE[e.typeId]) continue;
      const d = Math.hypot(
        e.location.x - player.location.x,
        e.location.y - player.location.y,
        e.location.z - player.location.z,
      );
      if (d < bestD) { bestD = d; best = e; }
    }
  } catch (e) {}
  return best;
}

function captureChance(target, bonus = 0) {
  let pct = 1;
  try {
    const hp = target.getComponent("minecraft:health");
    pct = hp ? hp.currentValue / Math.max(1, hp.effectiveMax) : 1;
  } catch (e) {}
  let c = 0.40 + (1 - pct) * 0.60;
  try {
    if (target.getEffect("slowness") || target.getEffect("poison") || target.getEffect("weakness")) c += 0.15;
  } catch (e) {}
  if (bonus >= 1) return 1;                       // 大師球
  return Math.min(0.95, Math.max(0.40, c + bonus));
}

// 拋出一顆球（讓球真的會減少；創造模式有些物品不會自動扣，這裡手動扣）
function consumeBall(player, ballId = BALL_ITEM) {
  try {
    const inv = player.getComponent("minecraft:inventory");
    const c = inv?.container;
    if (!c) return false;
    let slot = player.selectedSlotIndex ?? 0;
    let item = c.getItem(slot);
    if (!item || item.typeId !== ballId) {
      // 手上不是這顆球就找背包裡第一顆同款
      for (let i = 0; i < c.size; i++) {
        const it = c.getItem(i);
        if (it?.typeId === ballId) { slot = i; item = it; break; }
      }
    }
    if (!item || item.typeId !== ballId) return false;
    const before = item.amount;
    if (item.amount <= 1) c.setItem(slot, undefined);
    else { item.amount -= 1; c.setItem(slot, item); }
    // 記錄伺服器端到底有沒有扣成功（創造模式下客戶端可能又補回來）
    try {
      const after = c.getItem(slot)?.amount ?? 0;
      console.log(`${TAG} 扣球 slot=${slot} ${ballId} ${before} -> ${after}`);
    } catch (e) {}
    return true;
  } catch (e) {
    console.log(`${TAG} consumeBall 失敗: ${e}`);
    return false;
  }
}

function giveSpawnEgg(player, typeId) {
  const eggId = `${typeId}_spawn_egg`;
  try {
    const stack = new ItemStack(eggId, 1);
    const inv = player.getComponent("minecraft:inventory");
    if (inv?.container) {
      if (inv.container.emptySlotsCount > 0) {
        inv.container.addItem(stack);
      } else {
        player.dimension.spawnItem(stack, player.location);
        player.sendMessage("§e背包滿了，生怪蛋掉在你腳邊。");
      }
      return eggId;
    }
  } catch (e) {
    console.log(`${TAG} 生怪蛋 ${eggId} 取不到：${e}`);
  }
  return null;
}

// ============================================================ 捕捉演出

const CATCH_JOBS = [];

// 判斷這隻是不是「玩家自己的」——自己的夥伴不能再被抓一次，
// 否則會出現「抓掉自己的召喚物 → 又拿到一顆蛋」的憑空繁殖
function isOwnedPoke(entity) {
  try {
    const tags = entity.getTags();
    if (tags.some((t) => t === FOLLOW_TAG || t.startsWith("powner_"))) return true;
  } catch (e) {}
  try {
    if (entity.getComponent("minecraft:tameable")?.isTamed) return true;
  } catch (e) {}
  return false;
}

function startCatchSequence(player, target, ballId = BALL_ITEM) {
  if (CATCH_JOBS.some((j) => j.player?.id === player.id)) {
    player.sendMessage("§7球還在飛，等一下。");
    return false;
  }
  if (isOwnedPoke(target)) {
    player.sendMessage("§e這是你自己的寶可夢，不能再收進球裡。");
    console.log(`${TAG} 拒絕捕捉：${target.typeId} 屬於 ${player.name}（自己召喚/馴服的）`);
    return false;
  }

  const chance = captureChance(target, BALL_BONUS[ballId] ?? 0);
  const ballName = BALL_NAMES[ballId] ?? "精靈球";
  const name = NAME_ZH[target.typeId] ?? target.typeId;
  let from;
  try {
    const dir = player.getViewDirection();
    from = { x: player.location.x + dir.x * 0.6, y: player.location.y + 1.3, z: player.location.z + dir.z * 0.6 };
  } catch (e) {
    from = { x: player.location.x, y: player.location.y + 1.3, z: player.location.z };
  }
  const to = { x: target.location.x, y: target.location.y + 0.8, z: target.location.z };
  CATCH_JOBS.push({ player, target, from, to, t: 0, stage: "fly", wobbles: 0, chance, name });
  try { player.dimension.playSound("random.bow", from, { volume: 1, pitch: 1.4 }); } catch (e) {}
  player.sendMessage(`§7你丟出了${ballName}…（成功率 ${Math.round(chance * 100)}%）`);
  console.log(`${TAG} 開始捕捉 ${target.typeId} 玩家=${player.name} 球=${ballName} 機率=${Math.round(chance * 100)}%`);
  return true;
}

function resolveCatch(player, target, chance, name) {
  const roll = Math.random();
  console.log(
    `${TAG} 捕獲判定 ${target?.typeId} 機率=${Math.round(chance * 100)}% 骰=${roll.toFixed(2)} -> ` +
    `${roll > chance ? "掙脫" : "成功"}`,
  );
  let dim;
  try { dim = player?.dimension ?? target?.dimension ?? world.getDimension("overworld"); } catch (e) {
    dim = world.getDimension("overworld");
  }

  if (roll > chance) {
    try { player?.sendMessage(`§e${name} 從球裡掙脫了！（成功率 ${Math.round(chance * 100)}%）`); } catch (e) {}
    try { dim.playSound("random.break", player?.location ?? target?.location); } catch (e) {}
    try { target?.applyDamage(1, { cause: "entityAttack" }); } catch (e) {}
    return false;
  }

  try {
    if (!target || !target.isValid) return false;
  } catch (e) {}
  if (isOwnedPoke(target)) {
    try { player?.sendMessage("§e這是你的寶可夢，球彈開了。"); } catch (e) {}
    return false;
  }

  const rawId = target.typeId;
  const typeId = baseOf(rawId);          // 圖鑑/生怪蛋一律記本體
  const shiny = isShinyId(rawId);
  const count = addToDex(typeId);
  let egg = null;
  try { egg = giveSpawnEgg(player, typeId); } catch (e) {}
  try {
    player?.setDynamicProperty("poke:partner", typeId);
    player?.setDynamicProperty("poke:partner_shiny", shiny ? "1" : "0");
  } catch (e) {}
  const loc = target.location;
  try { target.remove(); } catch (e) {}
  fx(dim, loc, "minecraft:basic_smoke_particle", "random.levelup", 1.2);
  try {
    player?.sendMessage(`§a捕獲成功！${shiny ? "§d✦異色§f" : ""}§f${name} §7（圖鑑 ${BASE_IDS.filter((id) => (readDex()[id] ?? 0) > 0).length}/${TOTAL_SPECIES}，這隻第 ${count} 次）`);
    if (egg) {
      player.sendMessage(`§7已放入 §f${name}§7 的生怪蛋 —— 拿在手上對地面點一下就能放出來。`);
      player.sendMessage(`§7或用 §f寶可夢圖鑑§7 點「召喚夥伴」，牠會跟著你走。`);
    }
  } catch (e) {}
  return true;
}

system.runInterval(() => {
  for (let i = CATCH_JOBS.length - 1; i >= 0; i--) {
    const j = CATCH_JOBS[i];
    j.t += 1;
    let dim = null;
    try { dim = j.player?.dimension ?? j.target?.dimension ?? world.getDimension("overworld"); } catch (e) {}

    try {
      if (dim && j.stage === "fly") {
        const p = Math.min(1, j.t / 8);
        const x = j.from.x + (j.to.x - j.from.x) * p;
        const z = j.from.z + (j.to.z - j.from.z) * p;
        const y = j.from.y + (j.to.y - j.from.y) * p + Math.sin(p * Math.PI) * 2.0;
        for (let k = 0; k < 3; k++) {
          try {
            dim.spawnParticle("minecraft:basic_flame_particle", {
              x: x + (Math.random() - 0.5) * 0.3,
              y: y + (Math.random() - 0.5) * 0.3,
              z: z + (Math.random() - 0.5) * 0.3,
            });
          } catch (e) {}
        }
        if (p >= 1) {
          j.stage = "wobble";
          j.t = 0;
          try { dim.playSound("mob.shulker.close", j.to, { volume: 1, pitch: 1.5 }); } catch (e) {}
          try { dim.spawnParticle("minecraft:basic_smoke_particle", j.to); } catch (e) {}
        }
      } else if (dim && j.stage === "wobble") {
        if (j.t % 7 === 0) {
          j.wobbles += 1;
          try { dim.playSound("random.click", j.to, { volume: 0.9, pitch: 1.1 + j.wobbles * 0.2 }); } catch (e) {}
          for (let k = 0; k < 5; k++) {
            try {
              dim.spawnParticle("minecraft:critical_hit_emitter", {
                x: j.to.x + (Math.random() - 0.5) * 1.4,
                y: j.to.y + Math.random() * 0.9,
                z: j.to.z + (Math.random() - 0.5) * 1.4,
              });
            } catch (e) {}
          }
        }
        if (j.wobbles >= 3) {
          CATCH_JOBS.splice(i, 1);
          resolveCatch(j.player, j.target, j.chance, j.name);
          continue;
        }
      }
      if (j.t > 120) {
        CATCH_JOBS.splice(i, 1);
        resolveCatch(j.player, j.target, j.chance, j.name);
      }
    } catch (e) {
      console.log(`${TAG} 捕捉動畫例外（強制結算）: ${e}`);
      CATCH_JOBS.splice(i, 1);
      try { resolveCatch(j.player, j.target, j.chance, j.name); } catch (err) {}
    }
  }
}, 2);

// ============================================================ 圖鑑面板

function showDex(player, page, deferred) {
  // 一律延到下一 tick 才開表單：從事件回呼直接 show() 會讓圖示貼圖載入失敗
  if (!deferred) {
    system.run(() => { try { showDex(player, page, true); } catch (e) {} });
    return;
  }
  const d = readDex();
  const caught = BASE_IDS.filter((id) => (d[id] ?? 0) > 0).length;
  let partner = "(無)";
  try { partner = player.getDynamicProperty("poke:partner") ?? "(無)"; } catch (e) {}

  // 聊天欄只留一行摘要（之前一次噴 59 行，會讓後面的表單圖示載入失敗）
  try {
    player.sendMessage(`§6寶可夢圖鑑 §f${caught}/${TOTAL_SPECIES} §7已捕獲　夥伴：§f${NAME_ZH[partner] ?? partner}`);
  } catch (e) {}

  const dexIcon = (id) => `textures/items/dex_${String(id).replace(/^poke:/, "")}`;

  const PAGE = 999;
  const pages = Math.max(1, Math.ceil(BASE_IDS.length / PAGE));
  const p = Math.max(0, Math.min(Number(page) || 0, pages - 1));
  const slice = BASE_IDS.slice(p * PAGE, p * PAGE + PAGE);

  try {
    const form = new ActionFormData()
      .title(pages > 1 ? `寶可夢圖鑑 ${p + 1}/${pages}` : "寶可夢圖鑑")
      .body(`已捕獲 ${caught}/${TOTAL_SPECIES}　§7（✦＝異色）\n夥伴：${NAME_ZH[partner] ?? partner}`);
    form.button("召喚夥伴", "textures/items/pokeball");
    form.button("收回夥伴", "textures/items/greatball");
    const dbg = [];
    for (const id of slice) {
      const n = d[id] ?? 0;
      const sh = (d[`${id}${SHINY_SUFFIX}`] ?? 0) > 0;
      const label = `${n > 0 ? "✔" : "✘"} ${NAME_ZH[id] ?? id}${n > 0 ? ` x${n}` : ""}${sh ? " ✦" : ""}`;
      const iconPath = dexIcon(sh ? `${id}${SHINY_SUFFIX}` : id);
      dbg.push(`${id}=${n}${sh ? "(shiny)" : ""} -> ${iconPath}`);
      form.button(label, iconPath);
    }
    console.log(`${TAG} 圖鑑第${p + 1}頁 icons: ${dbg.join(" | ")}`);
    console.log(`${TAG} 圖鑑 title=寶可夢圖鑑 ${p + 1}/${pages} body=已捕獲 ${caught}/${TOTAL_SPECIES} SHINY_SUFFIX=${SHINY_SUFFIX}`);
    const navStart = 2 + slice.length;
    if (p > 0) form.button("◀ 上一頁");
    if (p < pages - 1) form.button("下一頁 ▶");

    form.show(player).then((res) => {
      if (res.canceled) return;
      const sel = res.selection;
      if (sel === 0) { summonPartner(player); return; }
      if (sel === 1) { recallPartner(player); return; }
      if (sel >= 2 && sel < navStart) {
        const picked = slice[sel - 2];
        if (!picked) return;
        if (!(readDex()[picked] > 0)) {
          player.sendMessage(`§7你還沒抓過 ${NAME_ZH[picked] ?? picked}。`);
          return;
        }
        try { player.setDynamicProperty("poke:partner", picked); } catch (e) {}
        summonPartner(player);
        return;
      }
      let idx = sel - navStart;
      if (p > 0) {
        if (idx === 0) { showDex(player, p - 1); return; }
        idx -= 1;
      }
      if (p < pages - 1 && idx === 0) { showDex(player, p + 1); return; }
    }).catch((err) => {
      try { player.sendMessage(`${TAG} 圖鑑面板打不開：${err}`); } catch (e2) {}
    });
  } catch (e) {
    try { player.sendMessage(`${TAG} 圖鑑面板失敗：${e}`); } catch (e2) {}
  }
}

// ============================================================ 夥伴跟隨

const FOLLOW_TAG = "poke_follow";
const ownerTag = (player) => `powner_${player.id}`;

function summonPartner(player) {
  let partnerId = null;
  try { partnerId = player.getDynamicProperty("poke:partner"); } catch (e) {}
  if (!partnerId) {
    player.sendMessage("§7你還沒有夥伴 —— 先抓一隻寶可夢。");
    return;
  }
  let shiny = false;
  try { shiny = player.getDynamicProperty("poke:partner_shiny") === "1"; } catch (e) {}
  const spawnId = shiny ? `${partnerId}${SHINY_SUFFIX}` : partnerId;

  recallPartner(player, true);
  let loc;
  try {
    const dir = player.getViewDirection();
    loc = { x: player.location.x + dir.x * 1.6, y: player.location.y, z: player.location.z + dir.z * 1.6 };
  } catch (e) {
    loc = { x: player.location.x + 1.5, y: player.location.y, z: player.location.z };
  }
  try {
    const e = player.dimension.spawnEntity(spawnId, loc);
    e.addTag(FOLLOW_TAG);
    e.addTag(ownerTag(player));

    // 關鍵：設成「已馴服 + 主人是這位玩家」，之後走路交給 AI 的 follow_owner，
    // 不再用腳本硬拉（硬拉就是你看到的「被吸著走」和往上跳）
    let tamed = false;
    try {
      const tameable = e.getComponent("minecraft:tameable");
      if (tameable) {
        if (!tameable.isTamed) tameable.tame(player);
        tamed = tameable.isTamed;
      }
    } catch (err) {
      console.log(`${TAG} tame 失敗: ${err}`);
    }

    try { e.nameTag = NAME_ZH[spawnId] ?? spawnId; } catch (err) {}
    player.sendMessage(
      `§a${NAME_ZH[partnerId] ?? partnerId} 出來了！§7（會跟著你、幫你打怪${tamed ? "" : "；馴服失敗，退回簡易跟隨"}）`,
    );
    try { player.dimension.playSound("random.orb", player.location); } catch (err) {}
    console.log(`${TAG} 召喚夥伴 ${partnerId} 給 ${player.name} 馴服=${tamed}`);
  } catch (e) {
    player.sendMessage(`§c召喚失敗：${e}`);
    console.log(`${TAG} 召喚失敗: ${e}`);
  }
}

function recallPartner(player, silent = false) {
  let n = 0;
  try {
    for (const e of player.dimension.getEntities({ tags: [ownerTag(player)] })) {
      try { e.remove(); } catch (err) {}
      n++;
    }
  } catch (e) {}
  if (!silent) player.sendMessage(n ? "§7夥伴已收回。" : "§7附近沒有你的夥伴。");
  return n;
}

// 跟隨：正常情況完全交給 AI 的 follow_owner 自己走（有尋路、會繞障礙）。
// 腳本只在「真的跟丟了」或「玩家飛走了」時補救，避免出現被吸著走/空中亂跳。
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    let followers = [];
    try {
      followers = player.dimension.getEntities({ tags: [ownerTag(player)] });
    } catch (e) {
      continue;
    }
    for (const f of followers) {
      let dist;
      try {
        dist = Math.hypot(
          player.location.x - f.location.x,
          player.location.y - f.location.y,
          player.location.z - f.location.z,
        );
      } catch (e) {
        continue;
      }

      let tamed = false;
      try { tamed = f.getComponent("minecraft:tameable")?.isTamed ?? false; } catch (e) {}

      // 已馴服：AI 會自己跟，腳本只在超過 24 格（真跟丟）時拉一次
      // 未馴服：退回簡易模式，8 格才補位
      const limit = tamed ? 24 : 8;
      if (dist <= limit) continue;

      // 玩家飛到空中時不硬拉（避免牠在半空抽動），等玩家落地再補位
      let flying = false;
      try {
        const ground = player.dimension.getBlock({ x: player.location.x, y: player.location.y - 3, z: player.location.z });
        flying = !ground;                       // 腳下 3 格內沒方塊 = 在空中
      } catch (e) {}

      if (flying) continue;

      try {
        f.teleport({ x: player.location.x + 2.0, y: player.location.y, z: player.location.z }, { dimension: player.dimension });
        console.log(`${TAG} 夥伴距離 ${dist.toFixed(1)} 過遠，補位到玩家身邊`);
      } catch (e) {}
    }
  }
}, 20);

// 護主：① 玩者被打就反擊 ② 額外巡邏，附近有敵對怪就主動撲上去
const guardCooldown = new Map();

function followerAttack(follower, target) {
  const key = `${follower.id}:${target.id}`;
  const now = system.currentTick;
  if (now - (guardCooldown.get(key) ?? -9999) < 30) return false;
  guardCooldown.set(key, now);
  try {
    follower.teleport(
      { x: target.location.x + 1.2, y: target.location.y, z: target.location.z + 1.2 },
      { dimension: target.dimension },
    );
  } catch (e) {}
  // 讓客戶端播攻擊動作（屬性 client_sync，RP 的 animate 條件讀 poke:attack）
  try {
    follower.setProperty("poke:attack", true);
    system.runTimeout(() => {
      try { follower.setProperty("poke:attack", false); } catch (e) {}
    }, 12);
  } catch (e) {
    if (!globalThis.__pokePropWarned) {
      globalThis.__pokePropWarned = true;
      console.log(`${TAG} setProperty 失敗（攻擊動作不會播）: ${e}`);
    }
  }

  try {
    target.applyDamage(5, { cause: "entityAttack", damagingEntity: follower });
    try { target.dimension.spawnParticle("minecraft:critical_hit_emitter", target.location); } catch (e) {}
    if (follower.typeId === "poke:arceus" || follower.typeId === "poke:arceus_shiny") {
      fx(target.dimension, target.location, "minecraft:totem_particle", "random.levelup", 1.25);
      try {
        target.dimension.spawnParticle("minecraft:enchanting_table_particle", {
          x: target.location.x, y: target.location.y + 0.8, z: target.location.z,
        });
      } catch (e) {}
    }
    console.log(`${TAG} 夥伴 ${follower.typeId} 攻擊 ${target.typeId}`);
    return true;
  } catch (e) {
    console.log(`${TAG} 夥伴攻擊失敗: ${e}`);
    return false;
  }
}

world.afterEvents.entityHurt.subscribe((ev) => {
  try {
    const victim = ev.hurtEntity;
    const attacker = ev.damageSource?.damagingEntity;
    if (!victim || victim.typeId !== "minecraft:player" || !attacker) return;
    if (attacker.typeId === "minecraft:player") return;
    for (const f of victim.dimension.getEntities({ tags: [ownerTag(victim)] })) {
      followerAttack(f, attacker);
    }
  } catch (e) {}
});

// 尾巴火焰：腳本直接在世界座標發粒子（不吃 RP 動畫與 locator，最保險）
let tailFlameLogged = 0;
const TAIL_FLAME_TYPES = { "poke:charmander": { d: 0.62, h: 0.78 }, "poke:charizard": { d: 0.80, h: 1.15 } };
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    for (const typeId of Object.keys(TAIL_FLAME_TYPES)) {
      let ents = [];
      try {
        ents = player.dimension.getEntities({ type: typeId, location: player.location, maxDistance: 40 });
      } catch (e) {
        continue;
      }
      for (const e of ents) {
        try {
          if (tailFlameLogged < 3) { tailFlameLogged++; console.log(`${TAG} 尾巴火焰：${typeId} @ ${e.location.x.toFixed(1)},${e.location.y.toFixed(1)},${e.location.z.toFixed(1)}`); }
          const dir = e.getViewDirection();
          const cfg = TAIL_FLAME_TYPES[typeId];
          const tail = {
            x: e.location.x - dir.x * cfg.d,
            y: e.location.y + cfg.h,
            z: e.location.z - dir.z * cfg.d,
          };
          player.dimension.spawnParticle("minecraft:basic_flame_particle", tail);
          if (Math.random() < 0.5) {
            player.dimension.spawnParticle("minecraft:basic_smoke_particle", {
              x: tail.x, y: tail.y + 0.25, z: tail.z,
            });
          }
        } catch (e2) {}
      }
    }
  }
}, 6);

// 巡邏：每 20 tick 掃一次玩者周圍 12 格的敵對生物，夥伴主動出擊
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    let followers = [];
    try {
      followers = player.dimension.getEntities({ tags: [ownerTag(player)] });
    } catch (e) {
      continue;
    }
    if (!followers.length) continue;

    let monsters = [];
    try {
      monsters = player.dimension.getEntities({ location: player.location, maxDistance: 12 });
    } catch (e) {
      continue;
    }
    const hostile = monsters.filter((m) => {
      if (POKE_TYPE[m.typeId]) return false;
      if (m.typeId === "minecraft:player") return false;
      const id = m.typeId.replace("minecraft:", "");
      return /zombie|skeleton|creeper|spider|enderman|witch|slime|pillager|vindicator|ravager|hoglin|piglin|blaze|ghast|phantom|drowned|husk|stray|silverfish|guardian|shulker|wither|warden/i.test(id);
    });
    if (!hostile.length) continue;
    hostile.sort((a, b) => a.location.y - b.location.y);
    for (const f of followers) followerAttack(f, hostile[0]);
  }
}, 20);

// ============================================================ 異色（shiny）

const SHINY_CHANCE = 1 / 64;          // 野外生成時 1/64 機率變成異色

world.afterEvents.entitySpawn.subscribe((ev) => {
  try {
    const e = ev.entity;
    if (!e || ev.cause !== "Spawned") return;
    const id = e.typeId;
    if (!POKE_TYPE[id] || isShinyId(id)) return;
    if (Math.random() > SHINY_CHANCE) return;
    const loc = e.location;
    const dim = e.dimension;
    try { e.remove(); } catch (err) { return; }
    const shiny = dim.spawnEntity(`${id}${SHINY_SUFFIX}`, loc);
    console.log(`${TAG} 異色出現！${id} -> ${shiny.typeId}`);
    try {
      for (const p of dim.getPlayers({ location: loc, maxDistance: 32 })) {
        p.sendMessage(`§d✦ 異色 ${NAME_ZH[shiny.typeId] ?? shiny.typeId} 出現了！✦`);
        try { p.playSound("random.levelup"); } catch (err) {}
      }
    } catch (err) {}
  } catch (e) {}
});



// ---------------------------------------------------------------- 回復道具（基礎）

function consumeOne(player, typeId) {
  return consumeBall(player, typeId);        // 與丟球共用「扣一個」邏輯
}

function nearestOwnPoke(player, radius = 12) {
  let best = null;
  let bestD = Infinity;
  try {
    for (const e of player.dimension.getEntities({ tags: [ownerTag(player)] })) {
      const d = Math.hypot(
        e.location.x - player.location.x,
        e.location.y - player.location.y,
        e.location.z - player.location.z,
      );
      if (d < bestD) { bestD = d; best = e; }
    }
  } catch (e) {}
  if (best) return best;
  try {
    for (const e of player.dimension.getEntities({ location: player.location, maxDistance: radius })) {
      if (POKE_TYPE[e.typeId] && isOwnedPoke(e)) return e;
    }
  } catch (e) {}
  return null;
}

function usePotion(player, item) {
  const pet = nearestOwnPoke(player);
  if (!pet) {
    player.sendMessage("§7附近沒有你的寶可夢（先召喚夥伴再餵藥）。");
    return;
  }
  try {
    const hp = pet.getComponent("minecraft:health");
    const before = hp.currentValue;
    hp.setCurrentValue(Math.min(hp.effectiveMax, before + 60));
    try { pet.dimension.spawnParticle("minecraft:heart_particle", pet.location); } catch (e) {}
    player.sendMessage(`§a${NAME_ZH[pet.typeId] ?? pet.typeId} 回復了 §f${Math.round(hp.currentValue - before)}§a 點生命`);
    consumeOne(player, item.typeId);
  } catch (e) {
    player.sendMessage(`§c餵藥失敗：${e}`);
  }
}

function useRareCandy(player, item) {
  const pet = nearestOwnPoke(player);
  if (!pet) {
    player.sendMessage("§7附近沒有你的寶可夢（先召喚夥伴再餵糖）。");
    return;
  }
  try {
    const hp = pet.getComponent("minecraft:health");
    hp.setCurrentValue(hp.effectiveMax);
    pet.addEffect("strength", 6000, { amplifier: 1 });
    pet.addEffect("resistance", 6000, { amplifier: 0 });
    try {
      pet.dimension.spawnParticle("minecraft:totem_particle", pet.location);
      pet.dimension.playSound("random.levelup", pet.location);
    } catch (e) {}
    player.sendMessage(`§d${NAME_ZH[pet.typeId] ?? pet.typeId} 吃下神奇糖果：全回復 + 力量/抗性 5 分鐘！`);
    consumeOne(player, item.typeId);
  } catch (e) {
    player.sendMessage(`§c餵糖失敗：${e}`);
  }
}

// ---------------------------------------------------------------- 更多消耗品

const BERRY_HEAL = {
  "poke:berry": 6, "poke:oran_berry": 10, "poke:sitrus_berry": 16, "poke:lum_berry": 20,
  "poke:leppa_berry": 8, "poke:aguav_berry": 12, "poke:rawst_berry": 12,
  "poke:moomoo_milk": 20, "poke:revival_herb": 30,
};

const STONE_NAMES = {
  "poke:fire_stone": "火之石", "poke:water_stone": "水之石", "poke:thunder_stone": "雷之石",
  "poke:leaf_stone": "葉之石", "poke:moon_stone": "月之石", "poke:sun_stone": "日之石",
  "poke:shiny_stone": "光之石", "poke:dusk_stone": "暗之石", "poke:dawn_stone": "覺醒之石",
  "poke:ice_stone": "冰之石",
};

function useHealItem(player, item) {
  const amount = BERRY_HEAL[item.typeId];
  if (!amount) return;
  try {
    const hp = player.getComponent("minecraft:health");
    const before = hp.currentValue;
    hp.setCurrentValue(Math.min(hp.effectiveMax, before + amount));
    try { player.playSound("random.eat"); } catch (e) {}
    player.sendMessage(`§a回復 §f${Math.round(hp.currentValue - before)}§a 點生命`);
    consumeOne(player, item.typeId);
  } catch (e) {}
}

function useStone(player, item) {
  const pet = nearestOwnPoke(player);
  if (!pet) {
    player.sendMessage("§7附近沒有你的寶可夢（先召喚夥伴再用進化石）。");
    return;
  }
  const zh = STONE_NAMES[item.typeId] ?? "進化石";
  try {
    const hp = pet.getComponent("minecraft:health");
    hp.setCurrentValue(hp.effectiveMax);
    pet.addEffect("strength", 4800, { amplifier: 2 });
    pet.addEffect("resistance", 4800, { amplifier: 1 });
    pet.addEffect("speed", 4800, { amplifier: 1 });
    pet.dimension.spawnParticle("minecraft:totem_particle", pet.location);
    pet.dimension.playSound("random.levelup", pet.location);
    player.sendMessage(`§d${NAME_ZH[pet.typeId] ?? pet.typeId} 吸收了${zh}的力量！（全回復 + 攻防速強化 4 分鐘）`);
    consumeOne(player, item.typeId);
  } catch (e) {
    player.sendMessage(`§c使用失敗：${e}`);
  }
}

// ---------------------------------------------------------------- 方塊互動

const BLOCK_HEAL = "poke:healing_machine";
const BLOCK_PC = "poke:pc";

function onUseBlock(player, block) {
  if (!block) return false;
  const id = block.typeId;
  if (id === BLOCK_HEAL) {
    let healed = 0;
    try {
      const hp = player.getComponent("minecraft:health");
      hp.setCurrentValue(hp.effectiveMax);
      healed++;
    } catch (e) {}
    const pet = nearestOwnPoke(player, 16);
    if (pet) {
      try {
        pet.getComponent("minecraft:health").setCurrentValue(pet.getComponent("minecraft:health").effectiveMax);
        healed++;
      } catch (e) {}
    }
    try {
      player.dimension.spawnParticle("minecraft:heart_particle", block.center());
      player.playSound("random.levelup");
    } catch (e) {}
    player.sendMessage(`§a治療台啟動！回復了 ${healed} 個目標的生命。`);
    console.log(`${TAG} 治療台使用 player=${player.name} 回復=${healed}`);
    return true;
  }
  if (id === BLOCK_PC) {
    showDex(player);
    try { player.playSound("random.click"); } catch (e) {}
    console.log(`${TAG} PC 使用 player=${player.name}`);
    return true;
  }
  return false;
}

// ============================================================ 物品使用

function handleItemUse(ev, from) {
  try {
    const item = ev.itemStack;
    const player = ev.source ?? ev.player;
    if (!player || player.typeId !== "minecraft:player") return;
    const heldBall = item ? isBall(item.typeId) : false;

    // 方塊互動（手上不是球時才觸發，免得想丟球卻治療）
    if (ev.block && !heldBall) {
      if (onUseBlock(player, ev.block)) return;
    }
    if (!item) return;

    if (heldBall) {
      console.log(`${TAG} ${from}: 用${BALL_NAMES[item.typeId]} player=${player.name}`);
      const target = nearestPoke(player, 12);
      if (!target) {
        player.sendMessage("§7附近 12 格內沒有寶可夢（要站近一點再丟）。");
        return;
      }
      if (!startCatchSequence(player, target, item.typeId)) return;
      consumeBall(player, item.typeId);
    } else if (item.typeId === DEX_ITEM) {
      console.log(`${TAG} ${from}: 用圖鑑 player=${player.name}`);
      showDex(player);
    } else if (item.typeId === "poke:potion") {
      usePotion(player, item);
    } else if (item.typeId === "poke:rarecandy") {
      useRareCandy(player, item);
    } else if (BERRY_HEAL[item.typeId]) {
      useHealItem(player, item);
    } else if (STONE_NAMES[item.typeId]) {
      useStone(player, item);
    }
  } catch (e) {
    console.log(`${TAG} itemUse error: ${e}`);
  }
}

for (const evName of ["itemUse", "playerInteractWithBlock", "itemUseOn"]) {
  try {
    const ev = world.afterEvents[evName];
    if (ev && typeof ev.subscribe === "function") {
      ev.subscribe((e) => handleItemUse(e, evName));
      console.log(`${TAG} 已掛鉤 ${evName}`);
    } else {
      console.log(`${TAG} 沒有 ${evName} 事件`);
    }
  } catch (e) {
    console.log(`${TAG} 掛鉤 ${evName} 失敗: ${e}`);
  }
}

// ============================================================ 測試 / 管理指令

function say(target, msg) {
  try {
    if (target && target.typeId === "minecraft:player") target.sendMessage(msg);
  } catch (e) {}
  console.log(msg);
}

function handlePokeSub(sub, src) {  const dim = world.getDimension("overworld");
  const base = src && src.location ? src.location : { x: 0, y: 100, z: 0 };

  if (sub === "help") {
    for (const line of [
      "§6[Poke] 指令：",
      " §f/scriptevent poke:list §7列出寶可夢與招式",
      " §f/scriptevent poke:catch §7對最近 20 格的寶可夢丟球（自己執行）",
      " §f/scriptevent poke:partner §7召喚夥伴",
      " §f!dex / !dexprobe / !flametest / !icontest §7聊天版指令（不需權限）",
      " §f/scriptevent poke:recall §7收回夥伴",
      " §f/scriptevent poke:dex §7顯示圖鑑",
      " §f/scriptevent poke:dex_reset §7清空圖鑑",
      " §f/scriptevent poke:demo_all §7全部招式各測一次",
      " §f/scriptevent poke:type_test §7屬性克制驗證",
      " §f/scriptevent poke:sim §7模擬捕獲（機率/圖鑑/生怪蛋）",
      " §f/scriptevent poke:items §7檢查物品是否註冊",
      " §f/scriptevent poke:cleanballs §7清掉地上散落的精靈球",
    ]) say(src, line);
    return;
  }

  if (sub === "list") {
    for (const [id, move] of Object.entries(ABILITY)) say(src, `${TAG} ${id} (${POKE_TYPE[id]}) -> ${move}`);
    return;
  }

  if (sub === "items") {
    for (const id of [BALL_ITEM, "poke:greatball", "poke:ultraball", "poke:masterball", "poke:dusk_ball",
      "poke:quick_ball", "poke:beast_ball", "poke:fire_stone", "poke:shiny_stone", "poke:sitrus_berry",
      "poke:moomoo_milk", "poke:boulder_badge", "poke:potion", "poke:rarecandy", "poke:berry",
      DEX_ITEM, "poke:pikachu_spawn_egg"]) {
      try {
        new ItemStack(id, 1);
        say(src, `§a✔ ${id} 存在`);
      } catch (e) {
        say(src, `§c✘ ${id} 不存在（${e}）`);
      }
    }
    return;
  }

  if (sub === "icontest") {
    const f = new ActionFormData().title("圖示測試").body("哪幾個按鈕左邊有圖？記下字母告訴我。");
    f.button("A 香草 compass（應該有）", "textures/items/compass");
    f.button("B pokeball 16 調色盤（已知可以）", "textures/items/pokeball");
    f.button("C dex 128 無副檔名", "textures/items/dex_charizard");
    f.button("H flame16 16 調色盤", "textures/items/flame16_charizard");
    f.button("I flame32 32 調色盤", "textures/items/flame32_charizard");
    f.button("J flame64p 64 調色盤", "textures/items/flame64p_charizard");
    f.button("K flame64rgba 64 RGBA", "textures/items/flame64rgba_charizard");
    f.button("F portrait 64", "textures/items/portrait_charizard");
    f.button("D dex 128 帶 .png（對照）", "textures/items/dex_charizard.png");
    f.button("E ui 目錄 96 帶 .png（對照）", "textures/ui/dex_charizard.png");
    f.button("G 故意錯路徑（對照，應該缺圖）", "textures/items/definitely_not_here");
    f.show(src).catch((e) => say(src, `${TAG} icontest 失敗: ${e}`));
    return;
  }

  if (sub === "flametest") {
    const loc = src.location;
    const dim = src.dimension;
    let vd = { x: 0, z: 1 };
    try { vd = src.getViewDirection(); } catch (e) {}
    const rx = -vd.z, rz = vd.x;
    const bx = loc.x + vd.x * 3, bz = loc.z + vd.z * 3, by = loc.y + 1.2;
    const at = (k) => ({ x: bx + rx * k, y: by, z: bz + rz * k });
    const names = ["minecraft:basic_flame_particle", "minecraft:basic_smoke_particle", "poke:tail_flame"];
    const labels = ["自帶火焰", "自帶煙", "我們的火焰"];
    const ok = [];
    names.forEach((n, i) => {
      try { dim.spawnParticle(n, at(i * 1.2 - 1.2)); ok.push(`${labels[i]}=已發`); }
      catch (e) { ok.push(`${labels[i]}=失敗`); }
    });
    say(src, `§a前方三格，由左到右：${labels.join(" / ")}\n§7${ok.join("　")}`);
    console.log(`${TAG} flametest by ${src.name}: ${ok.join(" | ")}`);
    return;
  }

  if (sub === "chain") {
    const paths = [
      "textures/items/dex_pikachu", "textures/items/dex_eevee", "textures/items/dex_bulbasaur",
      "textures/items/dex_charmander", "textures/items/dex_squirtle", "textures/items/dex_jigglypuff",
    ];
    const withSec = "已捕獲 4/57　§7（✦＝異色）\n夥伴：(無)";
    const showNext = (n) => {
      if (n > 4) { say(src, "§a四個都看完了，告訴我哪幾個有圖。"); return; }
      const f = new ActionFormData();
      if (n === 2) { f.title("第2個：body 含顏色碼").body(withSec); }
      else if (n === 3) { f.title("寶可夢圖鑑 1/10").body("已捕獲 4/57"); }
      else if (n === 4) { f.title("第4個：前面多兩顆球").body("普通 body"); }
      else { f.title("第1個：乾淨對照").body("普通 body"); }
      if (n === 4) {
        f.button("召喚夥伴", "textures/items/pokeball");
        f.button("收回夥伴", "textures/items/greatball");
      }
      paths.forEach((pth, i) => f.button(`✔ 測試${i + 1}`, pth));
      f.show(src).then((r) => {
        if (r.canceled) { say(src, `§7你在第 ${n} 個按了取消`); return; }
        showNext(n + 1);
      }).catch((e) => { say(src, `第 ${n} 個表單失敗 ${e}`); showNext(n + 1); });
    };
    system.run(() => showNext(1));
    return;
  }

  if (sub === "dexprobe") {
    const f = new ActionFormData().title("圖鑑圖示探針").body("六行分別是：字面 charmander / 字面 pikachu / 函式算出 / 字面 charizard / 純圖示 / 帶顏色碼。告訴我哪幾行有圖。");
    f.button("1 字面 charmander", "textures/items/dex_charmander");
    f.button("2 字面 pikachu", "textures/items/dex_pikachu");
    f.button("3 函式 charmander", (() => { const id2 = "charmander"; return `textures/items/dex_${id2}`; })());
    f.button("4 字面 charizard 對照", "textures/items/dex_charizard");
    f.button("5 ✔ 小火龍 x1", "textures/items/dex_charmander");
    f.button("6 §a✔ §f小火龍 §7x1", "textures/items/dex_pikachu");
    f.show(src).catch((e) => say(src, `${TAG} dexprobe 失敗: ${e}`));
    return;
  }

  if (sub === "dex") {
    if (src && src.typeId === "minecraft:player") showDex(src);
    else say(src, JSON.stringify(readDex()));
    return;
  }

  if (sub === "cleanballs") {
    let n = 0;
    for (const d of [world.getDimension("overworld"), world.getDimension("nether"), world.getDimension("the_end")]) {
      try {
        for (const it of d.getEntities({ type: "minecraft:item" })) {
          try {
            if (it.getComponent("minecraft:item")?.itemStack?.typeId === "poke:pokeball") { it.remove(); n++; }
          } catch (e) {}
        }
      } catch (e) {}
    }
    say(src, `§a清掉地上 ${n} 顆精靈球`);
    return;
  }

  if (sub === "dex_reset") {
    writeDex({});
    say(src, "§a圖鑑已清空");
    return;
  }

  if (sub === "catch" || sub === "partner" || sub === "recall" || sub === "followinfo") {
    if (!src || src.typeId !== "minecraft:player") {
      console.log(`${TAG} ${sub} 需要玩家執行`);
      return;
    }
    if (sub === "catch") {
      const t = nearestPoke(src, 20);
      if (!t) { src.sendMessage("§7附近 20 格內沒有寶可夢。"); return; }
      startCatchSequence(src, t);
    } else if (sub === "partner") {
      summonPartner(src);
    } else if (sub === "recall") {
      recallPartner(src);
    } else {
      // 診斷：夥伴到底有沒有存在、標籤對不對、距離多少
      let fs = [];
      try { fs = src.dimension.getEntities({ tags: [ownerTag(src)] }); } catch (e) {}
      const lines = [`§6夥伴診斷：找到 ${fs.length} 隻`, `§7你的標籤：${ownerTag(src)}`];
      for (const f of fs) {
        let d = -1;
        try {
          d = Math.hypot(src.location.x - f.location.x, src.location.y - f.location.y, src.location.z - f.location.z);
        } catch (e) {}
        lines.push(`§7- ${f.typeId} 距離 ${d.toFixed(1)} 標籤 [${f.getTags().join(", ")}]`);
      }
      src.sendMessage(lines.join("\n"));
      lines.forEach((l) => console.log(l));
    }
    return;
  }

  const demoOne = (pokeId, victimId = "minecraft:chicken") => {
    const move = ABILITY[pokeId];
    if (!move) return;
    let self, victim;
    try {
      self = dim.spawnEntity(pokeId, { x: base.x + 2, y: base.y, z: base.z });
      victim = dim.spawnEntity(victimId, { x: base.x + 4, y: base.y, z: base.z });
    } catch (e) {
      console.log(`${TAG} 生成失敗（要有 tickingarea）: ${e}`);
      return;
    }
    const h = victim.getComponent("minecraft:health");
    const before = h?.currentValue;
    console.log(`${TAG} 測試 ${pokeId}(${POKE_TYPE[pokeId]}) -> ${move} 目標=${victimId} HP ${before}`);
    runMove(self, victim);
    const after = victim.getComponent("minecraft:health")?.currentValue ?? 0;
    console.log(`${TAG} 結果：${victimId} HP ${before} -> ${after}`);
    try { self.remove(); } catch (e) {}
    try { victim.remove(); } catch (e) {}
  };

  if (sub === "demo") {
    const keys = Object.keys(ABILITY);
    demoOne(keys[Math.floor(Math.random() * keys.length)]);
  } else if (sub === "demo_all") {
    Object.keys(ABILITY).forEach((k) => demoOne(k));
  } else if (sub === "type_test") {
    demoOne("poke:pikachu", "poke:squirtle");
    demoOne("poke:pikachu", "poke:charizard");
    demoOne("poke:charmander", "poke:bulbasaur");
    demoOne("poke:squirtle", "poke:charmander");
    demoOne("poke:gengar", "poke:mewtwo");
    demoOne("poke:eevee", "poke:gengar");
    demoOne("poke:mewtwo", "poke:pikachu");
  } else if (sub === "sim") {
    let t;
    try {
      t = dim.spawnEntity("poke:pikachu", { x: base.x + 2, y: base.y, z: base.z });
    } catch (e) {
      say(src, `${TAG} 生成失敗（要有 tickingarea）: ${e}`);
      return;
    }
    const hp = t.getComponent("minecraft:health");
    try { hp.setCurrentValue(Math.max(1, Math.floor(hp.effectiveMax * 0.3))); } catch (e) {}
    say(src, `${TAG} 模擬：pikachu HP ${hp.currentValue}/${hp.effectiveMax} 成功率 ${Math.round(captureChance(t) * 100)}%`);
    const n = addToDex(t.typeId);
    say(src, `${TAG} 圖鑑 +1（第 ${n} 次）`);
    let egg = "OK";
    try { new ItemStack("poke:pikachu_spawn_egg", 1); } catch (e) { egg = "FAIL " + e; }
    say(src, `${TAG} 生怪蛋 poke:pikachu_spawn_egg -> ${egg}`);
    try { t.remove(); } catch (e) {}
    writeDex({});
    say(src, `${TAG} 圖鑑已還原`);
  }

}

system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (!ev.id.startsWith("poke:")) return;
  try { handlePokeSub(ev.id.slice(5), ev.sourceEntity); } catch (e) { console.warn(`${TAG} scriptevent 失敗: ${e}`); }
});

// 註：這個 BDS 版本的 Script API 沒有 chatSend 事件，聊天觸發不可用，改用 /scriptevent

console.log(`${TAG} 初始化完成：招式 ${Object.keys(MOVES).length} 個、寶可夢 ${Object.keys(POKE_TYPE).length} 隻`);
