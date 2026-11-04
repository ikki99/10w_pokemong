import { world, system } from "@minecraft/server";

// ============================================================
// 主題世界入口：傳送廣場 + 各主題區域
// 只在「有鋪廣場的世界」啟用（中央 (0,-61,0) 是 lodestone 標記），
// 所以同一份腳本丟進其他世界不會亂傳人。
// ============================================================

const TAG = "[Worlds]";
const OW = "overworld";

// 站立高度（超平坦世界表面方塊是 y=-61）
const STAND_Y = -60;

const AREAS = {
  plaza:     { name: "傳送廣場", x: 0,   z: 0,   radius: 26 },
  city:      { name: "寶可夢城市", x: 400, z: 0, radius: 46 },
  studio:    { name: "建築練習場", x: 0,   z: 400, radius: 40 },
};

// pad：踩上去就傳送。enabled=false 的會提示「施工中」
const PADS = [
  { id: "to_city",   name: "寶可夢城市",  x: 0,   y: STAND_Y, z: -15, dest: { x: 400, y: STAND_Y, z: -22 }, enabled: true },
  { id: "to_studio", name: "建築練習場",  x: 0,   y: STAND_Y, z: 15,  dest: { x: 0,   y: STAND_Y, z: 376 },  enabled: true },
  { id: "to_zoo",    name: "動物園",      x: 15,  y: STAND_Y, z: 0,   enabled: false, hint: "動物園還在施工，之後開放" },
  { id: "to_ocean",  name: "海底世界",    x: -15, y: STAND_Y, z: 0,   enabled: false, hint: "海底世界還在施工，之後開放" },
  { id: "back_plaza", name: "回傳送廣場", x: 400, y: STAND_Y, z: -28, dest: { x: 0, y: STAND_Y, z: -8 }, enabled: true },
  { id: "studio_back", name: "回傳送廣場", x: 0,  y: STAND_Y, z: 372, dest: { x: 0, y: STAND_Y, z: 8 },  enabled: true },
];

// 各區域會生的寶可夢（先只做城市）
const AREA_SPAWNS = [
  {
    area: "city",
    limit: 10,
    pool: ["poke:pikachu", "poke:eevee", "poke:bulbasaur", "poke:charmander", "poke:squirtle",
           "poke:jigglypuff", "poke:meowth", "poke:psyduck", "poke:growlithe", "poke:lucario",
           "poke:gardevoir", "poke:mimikyu", "poke:sylveon"],
    shinyChanceBase: 0.02,
  },
];

let ACTIVE = false;
const cooldown = new Map();

function blockAt(x, y, z) {
  try {
    return world.getDimension(OW).getBlock({ x, y, z });
  } catch (e) {
    return undefined;
  }
}

// 用中央的 lodestone 當「這個世界有鋪廣場」的標記
function detect() {
  const b = blockAt(0, -61, 0);
  ACTIVE = !!b && (b.typeId === "minecraft:lodestone" || b.typeId === "poke:healing_machine");
  return ACTIVE;
}

function areaOfPlayer(p) {
  for (const [key, a] of Object.entries(AREAS)) {
    const dx = p.location.x - a.x;
    const dz = p.location.z - a.z;
    if (dx * dx + dz * dz <= a.radius * a.radius) return key;
  }
  return null;
}

function teleportTo(player, pad) {
  const d = pad.dest;
  player.teleport({ x: d.x + 0.5, y: d.y + 1, z: d.z + 0.5 }, { dimension: world.getDimension(OW) });
  try { player.playSound("random.orb", { pitch: 1.4, volume: 0.7 }); } catch (e) {}
  try {
    player.onScreenDisplay.setTitle(`§b${pad.name}`, {
      subtitle: "§7傳送完成", fadeInDuration: 5, stayDuration: 30, fadeOutDuration: 10,
    });
  } catch (e) {}
  console.log(`${TAG} 傳送 ${player.name} -> ${pad.name}`);
}

// 每 0.5 秒檢查玩家是不是站在傳送台上
system.runInterval(() => {
  if (!ACTIVE) return;
  let players = [];
  try { players = world.getAllPlayers(); } catch (e) { return; }
  const now = Date.now();
  for (const p of players) {
    for (const pad of PADS) {
      if (Math.abs(p.location.x - pad.x) > 1.6) continue;
      if (Math.abs(p.location.z - pad.z) > 1.6) continue;
      if (Math.abs(p.location.y - pad.y) > 2.2) continue;
      const key = `${p.id}:${pad.id}`;
      const last = cooldown.get(key) ?? 0;
      if (now - last < 4000) continue;
      cooldown.set(key, now);
      if (!pad.enabled) {
        try {
          p.onScreenDisplay.setActionBar(`§e${pad.hint ?? "施工中"} §7(${pad.name})`);
        } catch (e) {}
        continue;
      }
      teleportTo(p, pad);
      break;
    }
  }
}, 10);

// 地面高度：從 y=-59 往下找第一個不是空氣的方塊上方
function groundY(x, z) {
  for (let y = -58; y >= -64; y--) {
    const b = blockAt(Math.floor(x), y, Math.floor(z));
    if (b && b.typeId !== "minecraft:air" && b.typeId !== "minecraft:water") return y + 1;
  }
  return STAND_Y + 1;
}

function countNear(area, radius, prefix) {
  const c = { x: area.x, y: STAND_Y, z: area.z };
  try {
    const list = world.getDimension(OW).getEntities({ location: c, maxDistance: radius });
    return list.filter((e) => e.typeId.startsWith(prefix)).length;
  } catch (e) {
    return 0;
  }
}

// 每 5 秒補生：區域內有玩家、且數量不足才生
system.runInterval(() => {
  if (!ACTIVE) return;
  let players = [];
  try { players = world.getAllPlayers(); } catch (e) { return; }
  for (const cfg of AREA_SPAWNS) {
    const area = AREAS[cfg.area];
    if (!area) continue;
    const someone = players.some((p) => {
      const dx = p.location.x - area.x;
      const dz = p.location.z - area.z;
      return dx * dx + dz * dz <= (area.radius + 24) * (area.radius + 24);
    });
    if (!someone) continue;
    const have = countNear(area, area.radius + 8, "poke:");
    if (have >= cfg.limit) continue;
    const typeId = cfg.pool[Math.floor(Math.random() * cfg.pool.length)];
    const ang = Math.random() * Math.PI * 2;
    const dist = 10 + Math.random() * (area.radius - 12);
    const x = area.x + Math.cos(ang) * dist;
    const z = area.z + Math.sin(ang) * dist;
    try {
      const y = groundY(x, z);
      const e = world.getDimension(OW).spawnEntity(typeId, { x, y, z });
      // 低機率直接生異色版
      if (Math.random() < (cfg.shinyChanceBase ?? 0)) {
        const shinyId = `${typeId}_shiny`;
        try {
          e.remove();
          world.getDimension(OW).spawnEntity(shinyId, { x, y, z });
          console.log(`${TAG} 城市出現異色 ${shinyId}`);
        } catch (err) {}
      }
    } catch (e) {
      console.log(`${TAG} 生成失敗 ${typeId}: ${e}`);
    }
  }
}, 100);

// 啟動自檢 + 手動觸發
system.runTimeout(() => {
  const on = detect();
  console.log(`${TAG} 主題世界${on ? "已啟用" : "未啟用（此世界沒有廣場標記）"}，傳送台 ${PADS.length} 個`);
}, 40);

system.afterEvents.scriptEventReceive.subscribe((ev) => {
  if (ev.id === "world:pads") {
    const lines = PADS.map((p) => `${p.enabled ? "✔" : "✘"} ${p.name} @ ${p.x},${p.z}`);
    console.log(`${TAG} PADS\n${lines.join("\n")}`);
    ev.sourceEntity?.sendMessage?.(`§b傳送台：\n§f${lines.join("\n")}`);
  }
  if (ev.id === "world:goto" && ev.sourceEntity?.typeId === "minecraft:player") {
    const which = (ev.message || "").trim();
    const pad = PADS.find((p) => p.id === which || p.name === which);
    if (pad?.enabled) teleportTo(ev.sourceEntity, pad);
    else ev.sourceEntity.sendMessage(`§7沒有這個傳送台：${which}`);
  }
  if (ev.id === "world:reset") {
    ACTIVE = detect();
    ev.sourceEntity?.sendMessage?.(`§a主題世界已重新偵測：${ACTIVE ? "啟用" : "停用"}`);
  }
});

console.log(`${TAG} 模組載入：主題世界傳送（等待標記偵測）`);
