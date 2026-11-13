// Write simulator/anatomy.js: the head and neck shown in the 3D view.
//
// The shapes come from BodyParts3D (CC BY 4.0), as packaged for the web in the
// npm package "abussola-med-models" (see THIRD_PARTY.md). They are a picture
// only: nothing in the model reads them. This script is the one place in the
// repo that needs Node packages, and only when the picture is rebuilt:
//
//   npm install --no-save abussola-med-models@1.2.0 @gltf-transform/core @gltf-transform/extensions meshoptimizer
//   node scripts/build_anatomy.mjs
//
// The page build, the model and the tests use the file that is committed. It
// is a script, not plain JSON, so that the page can load it when opened
// straight from disk.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import { MeshoptDecoder, MeshoptSimplifier } from "meshoptimizer";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PACKAGE = path.join(ROOT, "node_modules", "abussola-med-models");
const OUT = path.join(ROOT, "simulator", "anatomy.js");

// The source is in metres: x to the person's left, y up, z forward.
// The page wants: face toward -x, y up, the person's left toward the viewer.
const UNITS_PER_METRE = 2300;
const CENTRE = { y: 1.585, z: -0.012 };          // the point the head turns about
const NECK_CUT = 1.427;                          // nothing below this height is kept
const NECK_HALF_WIDTH = 0.088;                   // trims the shoulders off the skin
const PINCH_HEIGHT = 1.468;                      // where the picture shows the carotids squeezed
const toScene = (x, y, z) => [-(z - CENTRE.z) * UNITS_PER_METRE, (y - CENTRE.y) * UNITS_PER_METRE, x * UNITS_PER_METRE];

// How many triangles each part may keep.
const BUDGET = { skin: 24000, skull: 20000, mandible: 2400, teeth: 6000, spine: 7000, cortex: 56000, whiteMatter: 5000,
  cerebellum: 9000, brainstem: 5000, arteries: 30000 };

await MeshoptDecoder.ready;
await MeshoptSimplifier.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ "meshopt.decoder": MeshoptDecoder });
const catalog = (name) => Object.fromEntries(JSON.parse(fs.readFileSync(path.join(PACKAGE, "detail", name))).map((x) => [x.key, x]));

// ---- small mesh helpers ------------------------------------------------------
// A mesh here is { p: positions in metres (flat), f: triangle indices, tag: one byte per point,
// value: one number per point (how deep in a fold, or how far along an artery) }.
function read(node, primitive, tagOf) {
  const m = node.getWorldMatrix(), pos = primitive.getAttribute("POSITION"), n = pos.getCount(), e = [0, 0, 0];
  const p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos.getElement(i, e);
    for (let k = 0; k < 3; k++) p[3 * i + k] = m[k] * e[0] + m[4 + k] * e[1] + m[8 + k] * e[2] + m[12 + k];
  }
  const f = Uint32Array.from(primitive.getIndices().getArray());
  const tag = new Uint8Array(n);
  if (tagOf) for (let i = 0; i < n; i++) tag[i] = tagOf(i);
  return { p, f, tag, value: new Float32Array(n) };
}
// Keep only the triangles whose three corners pass `keep`, and drop unused points.
function filter(mesh, keep) {
  const ok = new Uint8Array(mesh.p.length / 3);
  for (let i = 0; i < ok.length; i++) ok[i] = keep(i, mesh.p[3 * i], mesh.p[3 * i + 1], mesh.p[3 * i + 2]) ? 1 : 0;
  const f = [];
  for (let t = 0; t < mesh.f.length; t += 3) if (ok[mesh.f[t]] && ok[mesh.f[t + 1]] && ok[mesh.f[t + 2]]) f.push(mesh.f[t], mesh.f[t + 1], mesh.f[t + 2]);
  return compact({ ...mesh, f: Uint32Array.from(f) });
}
function compact(mesh) {
  const map = new Int32Array(mesh.p.length / 3).fill(-1), p = [], tag = [], value = [];
  const f = mesh.f.map((i) => {
    if (map[i] < 0) { map[i] = p.length / 3; p.push(mesh.p[3 * i], mesh.p[3 * i + 1], mesh.p[3 * i + 2]); tag.push(mesh.tag[i]); value.push(mesh.value[i]); }
    return map[i];
  });
  return { p: Float32Array.from(p), f, tag: Uint8Array.from(tag), value: Float32Array.from(value) };
}
// Merge points that sit in the same place (and carry the same tag), so shading is smooth across them.
function weld(mesh) {
  const seen = new Map(), map = new Uint32Array(mesh.p.length / 3);
  for (let i = 0; i < map.length; i++) {
    const key = `${Math.round(mesh.p[3 * i] * 2e5)},${Math.round(mesh.p[3 * i + 1] * 2e5)},${Math.round(mesh.p[3 * i + 2] * 2e5)},${mesh.tag[i]}`;
    if (!seen.has(key)) seen.set(key, i);
    map[i] = seen.get(key);
  }
  const f = [];
  for (let t = 0; t < mesh.f.length; t += 3) {
    const [a, b, c] = [map[mesh.f[t]], map[mesh.f[t + 1]], map[mesh.f[t + 2]]];
    if (a !== b && b !== c && a !== c) f.push(a, b, c);
  }
  return compact({ ...mesh, f: Uint32Array.from(f) });
}
function join(meshes) {
  const p = new Float32Array(meshes.reduce((n, m) => n + m.p.length, 0)), f = new Uint32Array(meshes.reduce((n, m) => n + m.f.length, 0));
  const tag = new Uint8Array(p.length / 3), value = new Float32Array(p.length / 3);
  let at = 0, fat = 0;
  for (const m of meshes) {
    p.set(m.p, at * 3); tag.set(m.tag, at); value.set(m.value, at);
    for (let i = 0; i < m.f.length; i++) f[fat + i] = m.f[i] + at;
    at += m.p.length / 3; fat += m.f.length;
  }
  return { p, f, tag, value };
}
// Loop subdivision: every triangle becomes four and the surface is rounded off.
// Used on the skin, which is coarse in the source model.
function subdivide(mesh) {
  const n = mesh.p.length / 3, P = mesh.p, key = (a, b) => (a < b ? a * n + b : b * n + a);
  const edges = new Map(), around = Array.from({ length: n }, () => new Set());
  for (let t = 0; t < mesh.f.length; t += 3) for (let k = 0; k < 3; k++) {
    const a = mesh.f[t + k], b = mesh.f[t + ((k + 1) % 3)], c = mesh.f[t + ((k + 2) % 3)];
    if (!edges.has(key(a, b))) edges.set(key(a, b), { a, b, across: [], at: 0 });
    edges.get(key(a, b)).across.push(c);
    around[a].add(b); around[b].add(a);
  }
  const rim = Array.from({ length: n }, () => []);                  // neighbours along an open edge of the surface
  for (const e of edges.values()) if (e.across.length !== 2) { rim[e.a].push(e.b); rim[e.b].push(e.a); }
  const out = [];
  for (let i = 0; i < n; i++) {
    const v = [P[3 * i], P[3 * i + 1], P[3 * i + 2]], sum = [0, 0, 0];
    const ring = rim[i].length ? rim[i] : [...around[i]], count = ring.length;
    for (const j of ring) for (let k = 0; k < 3; k++) sum[k] += P[3 * j + k];
    const share = rim[i].length ? (count === 2 ? 1 / 8 : 0) : count === 3 ? 3 / 16 : 3 / (8 * count);
    for (let k = 0; k < 3; k++) out.push((1 - count * share) * v[k] + share * sum[k]);
  }
  for (const e of edges.values()) {
    e.at = out.length / 3;
    const inside = e.across.length === 2;
    for (let k = 0; k < 3; k++) out.push(inside
      ? (3 / 8) * (P[3 * e.a + k] + P[3 * e.b + k]) + (1 / 8) * (P[3 * e.across[0] + k] + P[3 * e.across[1] + k])
      : (P[3 * e.a + k] + P[3 * e.b + k]) / 2);
  }
  const f = [];
  for (let t = 0; t < mesh.f.length; t += 3) {
    const [a, b, c] = [mesh.f[t], mesh.f[t + 1], mesh.f[t + 2]];
    const ab = edges.get(key(a, b)).at, bc = edges.get(key(b, c)).at, ca = edges.get(key(c, a)).at;
    f.push(a, ab, ca, b, bc, ab, c, ca, bc, ab, bc, ca);
  }
  return { p: Float32Array.from(out), f: Uint32Array.from(f), tag: new Uint8Array(out.length / 3), value: new Float32Array(out.length / 3) };
}
function simplify(mesh, triangles) {
  if (mesh.f.length / 3 <= triangles) return mesh;
  const [f] = MeshoptSimplifier.simplify(mesh.f, mesh.p, 3, triangles * 3, 0.05);
  return compact({ ...mesh, f });
}
const b64 = (a) => Buffer.from(a.buffer, a.byteOffset, a.byteLength).toString("base64");
// Pack a mesh for the page: 16-bit positions inside its own box, in page units.
function pack(mesh, withTag, withValue) {
  const n = mesh.p.length / 3, s = new Float32Array(n * 3), low = [1e9, 1e9, 1e9], high = [-1e9, -1e9, -1e9];
  for (let i = 0; i < n; i++) {
    const q = toScene(mesh.p[3 * i], mesh.p[3 * i + 1], mesh.p[3 * i + 2]);
    for (let k = 0; k < 3; k++) { s[3 * i + k] = q[k]; low[k] = Math.min(low[k], q[k]); high[k] = Math.max(high[k], q[k]); }
  }
  const packed = new Uint16Array(n * 3);
  for (let i = 0; i < n * 3; i++) packed[i] = Math.round(((s[i] - low[i % 3]) / (high[i % 3] - low[i % 3] || 1)) * 65535);
  const wide = n > 65535;
  const out = { points: n, triangles: mesh.f.length / 3, low: low.map((v) => +v.toFixed(2)), high: high.map((v) => +v.toFixed(2)),
    positions: b64(packed), wide, faces: b64(wide ? mesh.f : Uint16Array.from(mesh.f)) };
  if (withTag) out.tag = b64(mesh.tag);
  if (withValue) {                                // stored as 0..255 of the largest value
    const top = mesh.value.reduce((a, b) => Math.max(a, b), 1e-9);
    out.valueMax = +top.toFixed(2); out.value = b64(Uint8Array.from(mesh.value, (v) => Math.round((255 * Math.max(0, v)) / top)));
  }
  return out;
}
const centroid = (mesh, keep) => {
  const c = [0, 0, 0]; let n = 0;
  for (let i = 0; i < mesh.p.length / 3; i++) if (!keep || keep(mesh.p[3 * i], mesh.p[3 * i + 1], mesh.p[3 * i + 2], mesh.tag[i])) { for (let k = 0; k < 3; k++) c[k] += mesh.p[3 * i + k]; n++; }
  return c.map((v) => v / n);
};
const scenePoint = (c) => toScene(...c).map((v) => +v.toFixed(1));

// ---- the body's surface, from the whole-body model -----------------------------
const body = await io.read(path.join(PACKAGE, "models", "anatomy-male.glb"));
const skinNode = body.getRoot().listNodes().find((n) => n.getName() === "skin" && n.getMesh());
let skin = read(skinNode, skinNode.getMesh().listPrimitives()[0]);
skin = subdivide(weld(filter(skin, (i, x, y) => y > NECK_CUT && Math.abs(x) < NECK_HALF_WIDTH + 0.004)));

// ---- bones, one node per bone ----------------------------------------------------
const bones = await io.read(path.join(PACKAGE, "detail", "skeleton-male.glb"));
const boneCatalog = catalog("skeleton-catalog.json");
const boneGroup = (group, skip = /^$/) => join(bones.getRoot().listNodes()
  .filter((n) => n.getMesh() && boneCatalog[n.getName()]?.group === group && !skip.test(boneCatalog[n.getName()].label))
  .map((n) => read(n, n.getMesh().listPrimitives()[0])));
const skull = weld(boneGroup("skull")), mandible = weld(boneGroup("mandible")), teeth = weld(boneGroup("teeth"));
const spine = weld(filter(boneGroup("spine_cervical", /hyoid/i), (i, x, y) => y > NECK_CUT));

// ---- brain, from the organs file (one mesh, each point knows its named part) ------
function parts(doc, catalogName) {
  const node = doc.getRoot().listNodes().find((n) => n.getMesh()), primitive = node.getMesh().listPrimitives()[0];
  const keys = node.getExtras().parts, cat = catalog(catalogName), part = primitive.getAttribute("_PART");
  const info = keys.map((k) => cat[k]);
  const all = read(node, primitive, null), partOf = new Uint16Array(all.p.length / 3);
  for (let i = 0; i < partOf.length; i++) partOf[i] = part.getScalar(i);
  // One mesh per wanted part; `tagOf` gives the byte stored on every point of that part.
  const take = (want, tagOf = () => 0) => {
    const wanted = info.map((c) => (c && want(c) ? 1 : 0)), meshes = [];
    for (let k = 0; k < info.length; k++) {
      if (!wanted[k]) continue;
      const m = filter(all, (i) => partOf[i] === k);
      m.tag.fill(tagOf(info[k])); m.info = info[k];
      meshes.push(m);
    }
    return meshes;
  };
  return { take };
}
const organs = parts(await io.read(path.join(PACKAGE, "detail", "organs-male.glb")), "organs-catalog.json");
const BACK = 1;                                   // tag bit: this point belongs to the back (vertebral) zone
const isCortex = (c) => c.group === "brain" && /gyrus|lobe|lobule|insula/i.test(c.label);
const cortex = weld(join(organs.take(isCortex, (c) => (/occipital lobe/i.test(c.label) ? BACK : 0))));
const whiteMatter = weld(join(organs.take((c) => /^White matter of/i.test(c.label))));
const cerebellum = weld(join(organs.take((c) => c.label === "Cerebellum")));
const brainstem = weld(join(organs.take((c) => ["Pons", "Medulla oblongata", "Midbrain", "Peduncle of midbrain"].includes(c.label))));
const eyes = organs.take((c) => /^(Left|Right) sclera$/.test(c.label)).map((m) => {
  const c = centroid(m); let r = 0;
  for (let i = 0; i < m.p.length / 3; i++) r += Math.hypot(m.p[3 * i] - c[0], m.p[3 * i + 1] - c[1], m.p[3 * i + 2] - c[2]) / (m.p.length / 3);
  return { side: m.info.label.split(" ")[0].toLowerCase(), centre: scenePoint(c), radius: +(r * UNITS_PER_METRE).toFixed(1) };
});
// White matter sits under every lobe: each point takes the zone of the nearest cortex point (coarse search).
{
  const step = Math.max(1, Math.floor(cortex.p.length / 3 / 4000));
  for (let i = 0; i < whiteMatter.p.length / 3; i++) {
    let best = 1e9, zone = 0;
    for (let j = 0; j < cortex.p.length / 3; j += step) {
      const d = (cortex.p[3 * j] - whiteMatter.p[3 * i]) ** 2 + (cortex.p[3 * j + 1] - whiteMatter.p[3 * i + 1]) ** 2 + (cortex.p[3 * j + 2] - whiteMatter.p[3 * i + 2]) ** 2;
      if (d < best) { best = d; zone = cortex.tag[j]; }
    }
    whiteMatter.tag[i] = zone;
  }
}
// How deep each point of the cortex sits in a fold: its distance below the
// outermost surface seen in the same direction from the middle of the brain.
function foldDepth(mesh) {
  const c = centroid(mesh), n = mesh.p.length / 3, ROWS = 56, COLS = 112;
  const outer = new Float32Array(ROWS * COLS), cell = new Int32Array(n), radius = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const d = [mesh.p[3 * i] - c[0], mesh.p[3 * i + 1] - c[1], mesh.p[3 * i + 2] - c[2]];
    radius[i] = Math.hypot(...d);
    const row = Math.min(ROWS - 1, Math.floor((Math.acos(d[1] / radius[i]) / Math.PI) * ROWS));
    const col = Math.min(COLS - 1, Math.floor(((Math.atan2(d[2], d[0]) + Math.PI) / (2 * Math.PI)) * COLS));
    cell[i] = row * COLS + col;
    outer[cell[i]] = Math.max(outer[cell[i]], radius[i]);
  }
  for (let i = 0; i < n; i++) {
    const row = Math.floor(cell[i] / COLS), col = cell[i] % COLS; let top = 0;
    for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
      const r = row + dr; if (r < 0 || r >= ROWS) continue;
      top = Math.max(top, outer[r * COLS + ((col + dc + COLS) % COLS)]);
    }
    mesh.value[i] = Math.min(0.012, Math.max(0, top - radius[i])) * UNITS_PER_METRE;
  }
}
foldDepth(cortex);

// ---- arteries of the head and neck -------------------------------------------------
// Each named artery is put in the front (carotid) or back (vertebral) group by
// which trunk it is joined to in this model, not by a list of names: start at
// the internal carotids and at the vertebral and basilar arteries, and spread
// outward through arteries that touch. The communicating arteries join the two
// systems, so the spread does not pass through them.
const vessels = parts(await io.read(path.join(PACKAGE, "detail", "vessels-male.glb")), "vessels-catalog.json");
const NOT_TO_THE_BRAIN = /subclavian|brachiocephalic|thyro|costocervical|acromi|suprascapular|cervical artery|intercostal/i;
let arteries = vessels.take((c) => c.kind === "artery" && ["arteries_head", "carotid_l", "carotid_r"].includes(c.group) && !NOT_TO_THE_BRAIN.test(c.label));
const TOUCH = 0.0016;                             // metres: two arteries this close are joined
const cellOf = (x, y, z) => `${Math.floor(x / TOUCH)},${Math.floor(y / TOUCH)},${Math.floor(z / TOUCH)}`;
const cells = new Map();
arteries.forEach((m, a) => { for (let i = 0; i < m.p.length; i += 3) { const k = cellOf(m.p[i], m.p[i + 1], m.p[i + 2]); if (!cells.has(k)) cells.set(k, new Set()); cells.get(k).add(a); } });
const touching = arteries.map(() => new Set());
arteries.forEach((m, a) => {
  for (let i = 0; i < m.p.length; i += 3) {
    const [cx, cy, cz] = [m.p[i], m.p[i + 1], m.p[i + 2]].map((v) => Math.floor(v / TOUCH));
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
      const near = cells.get(`${cx + dx},${cy + dy},${cz + dz}`);
      if (near) for (const b of near) if (b !== a) touching[a].add(b);
    }
  }
});
const zone = arteries.map(() => -1), queue = [];
arteries.forEach((m, a) => {
  const label = m.info.label;
  if (/communicating/i.test(label)) zone[a] = -2;                         // not spread through
  else if (/(internal|common) carotid artery$/i.test(label)) { zone[a] = 0; queue.push(a); }
  else if (/vertebral artery$|^Basilar artery$/i.test(label)) { zone[a] = 1; queue.push(a); }
});
while (queue.length) { const a = queue.shift(); for (const b of touching[a]) if (zone[b] === -1) { zone[b] = zone[a]; queue.push(b); } }
const report = { front: [], back: [], joining: [], unreached: [] };
arteries.forEach((m, a) => {
  const label = m.info.label;
  if (zone[a] === -2) { report.joining.push(label); zone[a] = 0; }
  else if (zone[a] === -1) report.unreached.push(label);
  else report[zone[a] ? "back" : "front"].push(label);
  const trunk = /^Left common carotid/i.test(label) ? 2 : /^Right common carotid/i.test(label) ? 4 : 0;
  m.tag.fill((zone[a] === 1 ? BACK : 0) | trunk);
});
const reached = arteries.filter((m, a) => zone[a] >= 0);

// The source model has no artery between the top of each common carotid and
// the bottom of the internal carotid above it, and its vertebral arteries
// start partway up the neck. Those four stretches are filled in here with
// plain tubes so the picture shows one unbroken path. They are not anatomy.
function tubeMesh(path, radii, tag, sides = 10) {
  const n = path.length, p = new Float32Array(n * sides * 3), f = [];
  for (let i = 0; i < n; i++) {
    const a = path[Math.max(0, i - 1)], b = path[Math.min(n - 1, i + 1)];
    const t = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...t);
    for (let k = 0; k < 3; k++) t[k] /= len;
    const u = [t[1], -t[0], 0], ul = Math.hypot(...u) || 1;        // across the tube; the paths here run mostly upward
    const across = ul < 1e-6 ? [1, 0, 0] : u.map((v) => v / ul);
    const other = [t[1] * across[2] - t[2] * across[1], t[2] * across[0] - t[0] * across[2], t[0] * across[1] - t[1] * across[0]];
    for (let k = 0; k < sides; k++) {
      const angle = (2 * Math.PI * k) / sides, c = Math.cos(angle) * radii[i], d = Math.sin(angle) * radii[i];
      for (let j = 0; j < 3; j++) p[(i * sides + k) * 3 + j] = path[i][j] + across[j] * c + other[j] * d;
    }
  }
  for (let i = 0; i < n - 1; i++) for (let k = 0; k < sides; k++) {
    const a = i * sides + k, b = i * sides + ((k + 1) % sides);
    f.push(a, a + sides, b, b, a + sides, b + sides);
  }
  return { p, f: Uint32Array.from(f), tag: new Uint8Array(n * sides).fill(tag), value: new Float32Array(n * sides) };
}
// The middle and radius of an artery's open end: `top` picks the upper end.
function endOf(mesh, top) {
  let edge = top ? -9 : 9;
  for (let i = 1; i < mesh.p.length; i += 3) edge = top ? Math.max(edge, mesh.p[i]) : Math.min(edge, mesh.p[i]);
  const near = (x, y) => Math.abs(y - edge) < 0.004, c = centroid(mesh, near);
  let r = 0, n = 0;
  for (let i = 0; i < mesh.p.length; i += 3) if (near(0, mesh.p[i + 1])) { r += Math.hypot(mesh.p[i] - c[0], mesh.p[i + 2] - c[2]); n++; }
  return { c, r: r / n };
}
const named = (label) => reached.find((m) => m.info.label === label);
const added = [];
for (const [side, bit] of [["Left", 2], ["Right", 4]]) {
  const low = endOf(named(`${side} common carotid artery`), true), high = endOf(named(`${side} internal carotid artery`), false);
  const path = [], radii = [], steps = 14;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps, ease = t * t * (3 - 2 * t);               // leaves and arrives heading straight up
    path.push([low.c[0] + (high.c[0] - low.c[0]) * ease, low.c[1] - 0.003 + (high.c[1] - low.c[1] + 0.006) * t, low.c[2] + (high.c[2] - low.c[2]) * ease]);
    radii.push(low.r + (high.r - low.r) * t);
  }
  added.push(tubeMesh(path, radii, bit));
  const start = endOf(named(`${side} vertebral artery`), false), down = [];
  for (let y = start.c[1] + 0.003; y > NECK_CUT - 0.004; y -= 0.004) down.push([start.c[0], y, start.c[2]]);
  added.push(tubeMesh(down, down.map(() => start.r), BACK));
  console.log(`${side}: joined the carotid from height ${low.c[1].toFixed(3)} to ${high.c[1].toFixed(3)} m (radius ${(low.r * 1000).toFixed(1)} to ${(high.r * 1000).toFixed(1)} mm); vertebral extended down from ${start.c[1].toFixed(3)} m`);
}
const pieces = [...reached, ...added];
pieces.forEach((m, k) => m.value.fill(k));                       // remember which piece each point came from
arteries = weld(filter(join(pieces), (i, x, y) => y > NECK_CUT));
const pieceOf = Int32Array.from(arteries.value);

// How far along the arteries each point is from the bottom of the neck, measured
// over the surface of the tubes. The page uses it to draw pulses moving upward.
{
  const n = arteries.p.length / 3, P = arteries.p, links = Array.from({ length: n }, () => []);
  const dist = (a, b) => Math.hypot(P[3 * a] - P[3 * b], P[3 * a + 1] - P[3 * b + 1], P[3 * a + 2] - P[3 * b + 2]);
  for (let t = 0; t < arteries.f.length; t += 3) for (let k = 0; k < 3; k++) {
    const a = arteries.f[t + k], b = arteries.f[t + ((k + 1) % 3)];
    links[a].push(b); links[b].push(a);
  }
  const grid = new Map(), key = (x, y, z) => `${x},${y},${z}`;        // points of touching arteries are linked too
  const where = (i) => [0, 1, 2].map((k) => Math.floor(P[3 * i + k] / TOUCH));
  for (let i = 0; i < n; i++) { const k = key(...where(i)); if (!grid.has(k)) grid.set(k, []); grid.get(k).push(i); }
  for (let i = 0; i < n; i++) {
    const [cx, cy, cz] = where(i);
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++)
      for (const j of grid.get(key(cx + dx, cy + dy, cz + dz)) || []) if (pieceOf[j] !== pieceOf[i] && dist(i, j) < 2 * TOUCH) links[i].push(j);
  }
  const along = new Float64Array(n).fill(Infinity), heap = [];
  const push = (d, i) => { heap.push([d, i]); let k = heap.length - 1; while (k > 0) { const up = (k - 1) >> 1; if (heap[up][0] <= heap[k][0]) break; [heap[up], heap[k]] = [heap[k], heap[up]]; k = up; } };
  const pop = () => {
    const first = heap[0], last = heap.pop();
    if (heap.length) { heap[0] = last; let k = 0; for (;;) { let m = k; for (const c of [2 * k + 1, 2 * k + 2]) if (c < heap.length && heap[c][0] < heap[m][0]) m = c; if (m === k) break; [heap[m], heap[k]] = [heap[k], heap[m]]; k = m; } }
    return first;
  };
  for (let i = 0; i < n; i++) if (P[3 * i + 1] < NECK_CUT + 0.012) { along[i] = P[3 * i + 1] - NECK_CUT; push(along[i], i); }
  while (heap.length) {
    const [d, i] = pop();
    if (d > along[i]) continue;
    for (const j of links[i]) { const e = d + dist(i, j); if (e < along[j]) { along[j] = e; push(e, j); } }
  }
  let unreachedPoints = 0;
  const joined = [];
  for (let i = 0; i < n; i++) if (isFinite(along[i])) joined.push(i);
  for (let i = 0; i < n; i++) {
    if (!isFinite(along[i])) {                   // a loose piece takes the distance of the nearest joined point
      unreachedPoints++;
      let best = Infinity;
      for (const j of joined) { const d = dist(i, j); if (d < best) { best = d; along[i] = along[j] + d; } }
    }
    arteries.value[i] = along[i] * UNITS_PER_METRE;
  }
  console.log("artery points not joined to the neck:", unreachedPoints, "of", n);
}

// ---- places the labels point at -------------------------------------------------------
// The middle of one artery at a given height: the average of its points just above and just below.
const middleAt = (keep, height) => {
  for (let reach = 0.003; reach < 0.03; reach += 0.003) {
    const above = [], below = [];
    for (let i = 0; i < arteries.p.length / 3; i++) {
      const y = arteries.p[3 * i + 1];
      if (!keep(arteries.tag[i], arteries.p[3 * i], y) || Math.abs(y - height) > reach) continue;
      (y >= height ? above : below).push(i);
    }
    if (above.length && below.length) {
      const c = [0, 0, 0];
      for (const i of [...above, ...below]) for (let k = 0; k < 3; k++) c[k] += arteries.p[3 * i + k] / (above.length + below.length);
      return [c[0], height, c[2]];
    }
  }
  throw new Error(`no artery found at height ${height}`);
};
const trunk = (bit) => (tag) => (tag & 6) === bit;
const backSide = (sign) => (tag, x) => (tag & 1) === 1 && x * sign > 0.004;
const anchors = {
  pinch: { left: scenePoint(middleAt(trunk(2), PINCH_HEIGHT)), right: scenePoint(middleAt(trunk(4), PINCH_HEIGHT)) },
  carotid: { left: scenePoint(middleAt(trunk(2), NECK_CUT + 0.03)), right: scenePoint(middleAt(trunk(4), NECK_CUT + 0.03)) },
  vertebral: { left: scenePoint(middleAt(backSide(1), 1.492)), right: scenePoint(middleAt(backSide(-1), 1.492)) },
  frontOfBrain: { left: scenePoint(centroid(cortex, (x, y, z) => z > 0.03 && y > 1.655 && x > 0.02)), right: scenePoint(centroid(cortex, (x, y, z) => z > 0.03 && y > 1.655 && x < -0.02)) },
  backOfBrain: { left: scenePoint(centroid(cerebellum, (x) => x > 0.02)), right: scenePoint(centroid(cerebellum, (x) => x < -0.02)) },
  brainCentre: scenePoint(centroid(cortex)),
};

const meshes = { skin, skull, mandible, teeth, spine, cortex, whiteMatter, cerebellum, brainstem, arteries };
const out = {
  credit: "Anatomy: BodyParts3D, (c) The Database Center for Life Science, CC BY 4.0, via abussola-med-models 1.2.0 (CC BY 4.0). Cropped to the head and neck, simplified and repacked for this page.",
  unitsPerMetre: UNITS_PER_METRE, eyes, anchors, meshes: {},
};
for (const [name, mesh] of Object.entries(meshes)) {
  out.meshes[name] = pack(simplify(mesh, BUDGET[name]), ["cortex", "whiteMatter", "arteries"].includes(name), ["cortex", "arteries"].includes(name));
  console.log(name.padEnd(12), "triangles", String(mesh.f.length / 3).padStart(7), "->", String(out.meshes[name].triangles).padStart(6), "points", out.meshes[name].points);
}
fs.writeFileSync(OUT, `window.ANATOMY = ${JSON.stringify(out)};\n`);
console.log(`wrote ${OUT} (${(fs.statSync(OUT).size / 1024).toFixed(0)} KB)`);
for (const [k, v] of Object.entries(report)) console.log(`${k} (${v.length}): ${v.join("; ")}`);
console.log(JSON.stringify({ eyes, anchors }));
