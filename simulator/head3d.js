// A 3D head for the x-ray view, drawn with three.js. Illustration only.
//
// Every shape is built from the same hand-drawn side outlines as the flat
// "film" view (passed in as `A`), given depth with a few plain rules: an
// outline is turned into a solid by sweeping an oval across it, arteries are
// laid on the surface of the brain, and the folds are a noise pattern. None
// of it feeds the model. The only things driven by the model are the colour
// of each brain zone, the brightness and dot speed of each zone's arteries,
// the narrowing of the carotids and the eyelids (see ASSUMPTIONS.md, A13).
function buildHead3D(THREE, host, A) {
  "use strict";
  const V3 = THREE.Vector3;
  // Flat-view coordinates (x right, y down, in drawing pixels) to 3D. The
  // face points to -x, up is +y, and z runs from the far ear to the near ear.
  const at = (x, y, z = 0) => new V3(x - A.pivot[0], A.pivot[1] - y, z);
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  // Straight-line lookup through a list of [input, output] pairs.
  const table = (pairs) => (v) => {
    if (v <= pairs[0][0]) return pairs[0][1];
    for (let i = 1; i < pairs.length; i++) {
      if (v <= pairs[i][0]) {
        const [a, fa] = pairs[i - 1], [b, fb] = pairs[i];
        return fa + ((fb - fa) * (v - a)) / (b - a);
      }
    }
    return pairs[pairs.length - 1][1];
  };
  const dome = (top, widest, half) => (y) => half * Math.sqrt(Math.max(0, 1 - ((widest - y) / (widest - top)) ** 2));

  // ---- solids from side outlines ---------------------------------------------
  // Sweep an oval across a side outline: at each height the cross-section runs
  // from the outline's front edge to its back edge and is `halfWidth(y)` wide.
  // Options: `side` (+1 or -1) builds one half only, with a flat inner face
  // `gap` from the midline; `face` and `spread` keep a narrow ridge (nose,
  // lips, chin) standing out from a flatter front.
  function loft(poly, halfWidth, o = {}) {
    const rows = o.rows || 56, ring = o.ring || 48, inner = o.side ? 10 : 0;
    const nFront = o.nFront || 2, nBack = o.nBack || 2, gap = o.gap || 0;
    let top = Infinity, bottom = -Infinity;
    for (const p of poly) { top = Math.min(top, p[1]); bottom = Math.max(bottom, p[1]); }
    bottom = Math.min(bottom, o.yMax === undefined ? bottom : o.yMax);
    const span = (y) => {
      let a = Infinity, b = -Infinity;
      for (let i = 0; i < poly.length; i++) {
        const p = poly[i], q = poly[(i + 1) % poly.length];
        if ((p[1] - y) * (q[1] - y) > 0 || p[1] === q[1]) continue;
        const x = p[0] + ((y - p[1]) / (q[1] - p[1])) * (q[0] - p[0]);
        a = Math.min(a, x); b = Math.max(b, x);
      }
      return [a, b];
    };
    const oval = (c, n) => Math.sign(c) * Math.abs(c) ** (2 / n);
    const positions = [];
    const perRow = ring + inner;
    for (let r = 0; r < rows; r++) {
      const t = r / (rows - 1);
      const eased = o.openBottom ? 1 - Math.cos((t * Math.PI) / 2) : (1 - Math.cos(t * Math.PI)) / 2;
      const y = top + 0.5 + (bottom - top - 1) * eased;
      let [front, back] = span(y);
      if (!isFinite(front)) { front = back = poly[0][0]; }
      const ridge = o.face ? Math.max(0, o.face(y) - front) : 0;
      if (o.face) front = Math.max(front, Math.min(o.face(y), back - 1));
      // The first and last rows shrink to a point, so the solid is closed.
      const closed = r === 0 || (r === rows - 1 && !o.openBottom) ? 0.02 : 1;
      const xc = (front + back) / 2, rx = ((back - front) / 2) * closed, w = Math.max(halfWidth(y), 0.5) * closed;
      for (let k = 0; k < ring; k++) {
        const angle = o.side ? (Math.PI * k) / (ring - 1) : (2 * Math.PI * k) / ring;
        const c = Math.cos(angle), s = Math.sin(angle), n = c > 0 ? nFront : nBack;
        let x = xc - rx * oval(c, n);
        const z = o.side ? o.side * (gap + (w - gap) * Math.abs(s) ** (2 / n)) : w * oval(s, n);
        if (ridge && c > 0) x -= ridge * Math.exp(-((z / o.spread(y)) ** 2)) * Math.min(1, c * 3);
        positions.push(x - A.pivot[0], A.pivot[1] - y, z);
      }
      for (let k = 0; k < inner; k++) {             // flat inner face, back to front
        const x = xc + rx - (2 * rx * (k + 1)) / (inner + 1);
        positions.push(x - A.pivot[0], A.pivot[1] - y, o.side * gap);
      }
    }
    const index = [];
    for (let r = 0; r < rows - 1; r++) for (let k = 0; k < perRow; k++) {
      const a = r * perRow + k, b = r * perRow + ((k + 1) % perRow), c = a + perRow, d = b + perRow;
      index.push(a, c, b, b, c, d);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(index);
    geometry.computeVertexNormals();
    // How far the surface stands out from the midline at a point of the outline.
    geometry.userData.reach = (x, y) => {
      const [front, back] = span(clamp(y, top + 1, bottom - 1));
      if (!isFinite(front)) return gap;
      const xc = (front + back) / 2, rx = Math.max(1, (back - front) / 2);
      const u = clamp((x - xc) / rx, -0.97, 0.97), n = u < 0 ? nFront : nBack;
      return gap + (Math.max(halfWidth(y), 0.5) - gap) * (1 - Math.abs(u) ** n) ** (1 / n);
    };
    return geometry;
  }

  // A tube along a path whose radius can change along its length.
  function tube(points, radii, sides = 8) {
    const n = points.length, positions = new Float32Array(n * sides * 3), index = [];
    const frames = points.map((p, i) => {
      const t = points[Math.min(n - 1, i + 1)].clone().sub(points[Math.max(0, i - 1)]).normalize();
      const ref = Math.abs(t.z) > 0.9 ? new V3(1, 0, 0) : new V3(0, 0, 1);
      const u = new V3().crossVectors(t, ref).normalize();
      return [u, new V3().crossVectors(t, u)];
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    for (let i = 0; i < n - 1; i++) for (let k = 0; k < sides; k++) {
      const a = i * sides + k, b = i * sides + ((k + 1) % sides);
      index.push(a, b, a + sides, b, b + sides, a + sides);
    }
    geometry.setIndex(index);
    geometry.userData.shape = (r) => {
      for (let i = 0; i < n; i++) for (let k = 0; k < sides; k++) {
        const angle = (2 * Math.PI * k) / sides, [u, v] = frames[i], p = points[i];
        const cu = Math.cos(angle) * r[i], cv = Math.sin(angle) * r[i], j = (i * sides + k) * 3;
        positions[j] = p.x + u.x * cu + v.x * cv; positions[j + 1] = p.y + u.y * cu + v.y * cv; positions[j + 2] = p.z + u.z * cu + v.z * cv;
      }
      geometry.attributes.position.needsUpdate = true;
      geometry.computeVertexNormals();
    };
    geometry.userData.shape(radii);
    return geometry;
  }

  // ---- materials -------------------------------------------------------------
  // Glass-like shell: nearly clear face-on, bright where it turns edge-on.
  const VIEW_VERTEX = `
    varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying vec3 vOut;
    void main() {
      vec4 eye = modelViewMatrix * vec4(position, 1.0);
      vNormal = normalMatrix * normal; vView = -eye.xyz; vPlace = position; vOut = normal;
      gl_Position = projectionMatrix * eye;
    }`;
  const shell = (color, base, gain, power) => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uBase: { value: base }, uGain: { value: gain }, uPower: { value: power } },
    vertexShader: VIEW_VERTEX,
    fragmentShader: `
      uniform vec3 uColor; uniform float uBase, uGain, uPower; varying vec3 vNormal; varying vec3 vView; varying vec3 vOut;
      void main() {
        float edge = 1.0 - abs(dot(normalize(vNormal), normalize(vView)));
        float level = 1.0 - 0.8 * pow(abs(normalize(vOut).y), 3.0);     // flat floors and ceilings are toned down
        gl_FragColor = vec4(uColor * (uBase + uGain * pow(edge, uPower)) * level, 1.0);
      }`,
    blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, side: THREE.DoubleSide,
  });
  const SKIN = shell(0x9cc8ee, 0.012, 0.42, 2.8), BONE = shell(0xd2e6f8, 0.02, 0.34, 2.4), DENSE = shell(0xe4f0fb, 0.07, 0.32, 1.5);
  // Solid, softly lit surface for things that must hide what is behind them.
  const solid = (color, side = THREE.DoubleSide) => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) } },
    vertexShader: VIEW_VERTEX,
    fragmentShader: `
      uniform vec3 uColor; varying vec3 vNormal; varying vec3 vView;
      void main() {
        float facing = abs(dot(normalize(vNormal), normalize(vView)));
        gl_FragColor = vec4(uColor * (0.4 + 0.8 * facing), 1.0);
      }`,
    side,
  });
  // Brain tissue: the colour is set from the model. The folds of the cerebrum
  // come from the film view's own drawing of them, laid on from three sides.
  const foldMap = new THREE.CanvasTexture(A.folds.canvas);
  foldMap.wrapS = foldMap.wrapT = THREE.MirroredRepeatWrapping; foldMap.anisotropy = 4;
  const tissue = (kind) => new THREE.ShaderMaterial({
    uniforms: {
      uFront: { value: new THREE.Color() }, uBack: { value: new THREE.Color() }, uMap: { value: foldMap },
      uBox: { value: new THREE.Vector3(A.folds.x - A.pivot[0], A.pivot[1] - A.folds.y, A.folds.size) },
      uBlend: { value: new THREE.Vector2(A.zoneBlend[0] - A.pivot[0], A.zoneBlend[1] - A.pivot[0]) }, uKind: { value: kind },
    },
    vertexShader: `
      varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying vec3 vOut;
      void main() {
        vec4 eye = modelViewMatrix * vec4(position, 1.0);
        vNormal = normalMatrix * normal; vView = -eye.xyz; vPlace = position; vOut = normal;
        gl_Position = projectionMatrix * eye;
      }`,
    fragmentShader: `
      uniform vec3 uFront, uBack, uBox; uniform vec2 uBlend; uniform float uKind; uniform sampler2D uMap;
      varying vec3 vNormal; varying vec3 vView; varying vec3 vPlace; varying vec3 vOut;
      float hash(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
      float noise(vec3 p) {
        vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
        return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
                   mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
      }
      // The fold drawing, looked up by a point given in the drawing's own plane.
      vec2 sample2(vec2 at) {
        vec2 uv = vec2((at.x - uBox.x) / uBox.z, 1.0 - (uBox.y - at.y) / uBox.z);
        float h = texture2D(uMap, uv).r;
        float tilt = texture2D(uMap, uv + vec2(-0.004, 0.004)).r - texture2D(uMap, uv + vec2(0.004, -0.004)).r;
        return vec2(h, tilt);
      }
      void main() {
        vec3 n = normalize(vNormal), v = normalize(vView);
        if (dot(n, v) < 0.0) n = -n;
        float h = 1.0, tilt = 0.0;
        if (uKind < 0.5) {
          vec3 w = pow(abs(normalize(vOut)), vec3(6.0)); w /= (w.x + w.y + w.z);
          vec2 f = w.z * sample2(vPlace.xy) + w.y * sample2(vec2(vPlace.x, 200.0 - abs(vPlace.z))) + w.x * sample2(vec2(30.0 + vPlace.z, vPlace.y));
          h = f.x; tilt = f.y;
        } else if (uKind < 1.5) {
          h = smoothstep(0.0, 0.6, abs(sin(vPlace.y * 0.62 + 3.0 * noise(vPlace * 0.02))));       // cerebellum: fine leaves
        }
        float lit = 0.36 + 0.64 * max(dot(n, normalize(vec3(-0.45, 0.6, 0.66))), 0.0);
        float rim = pow(1.0 - max(dot(n, v), 0.0), 2.5);
        vec3 colour = uKind > 0.5 ? uBack : mix(uFront, uBack, smoothstep(uBlend.x, uBlend.y, vPlace.x));
        gl_FragColor = vec4(colour * lit * (0.34 + 0.66 * h) * (1.0 + 1.6 * tilt) + colour * rim * 0.22, 1.0);
      }`,
    side: THREE.DoubleSide,
  });

  // ---- scene ------------------------------------------------------------------
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  host.appendChild(renderer.domElement);
  const scene = new THREE.Scene(), model = new THREE.Group();
  scene.add(model);
  const camera = new THREE.PerspectiveCamera(30, A.size[0] / A.size[1], 200, 6000);
  camera.position.set(0, 0, (A.size[1] / 2) / Math.tan((15 * Math.PI) / 180));
  const add = (geometry, material, order = 0) => { const m = new THREE.Mesh(geometry, material); m.renderOrder = order; model.add(m); return m; };
  const place = (mesh, x, y, z) => { mesh.position.copy(at(x, y, z)); return mesh; };

  // Skin. The face is a flatter front with the nose, lips and chin standing out as a ridge.
  const faceLine = table([[396, 240], [430, 245], [470, 243], [510, 237], [535, 229], [560, 223], [585, 221], [610, 222], [640, 225], [675, 233], [692, 250]]);
  const ridgeSpread = table([[400, 13], [500, 24], [526, 30], [540, 46], [600, 48], [640, 54], [690, 60]]);
  const headWide = (y) => (y < 300 ? dome(A.top.head, 300, 178)(y)
    : table([[300, 178], [380, 175], [440, 163], [500, 148], [570, 132], [640, 122], [700, 118], [800, 122], [905, 150]])(y));
  add(loft(A.head, headWide, { rows: 90, ring: 64, yMax: 905, openBottom: true, nFront: 2.5, nBack: 2.2, face: (y) => (y > 396 && y < 692 ? faceLine(y) : -1e9), spread: ridgeSpread }), SKIN, 5);
  for (const side of [-1, 1]) {                       // outer ears
    const ear = add(new THREE.TorusGeometry(26, 7, 8, 28), SKIN, 5);
    place(ear, 478, 468, side * (headWide(468) + 3));
    ear.scale.set(0.72, 1.3, 0.3); ear.rotation.set(0, side * -0.25, 0.12);
  }

  // Bone: skull, face, jaw, teeth, neck bones.
  const skullWide = (y) => (y < 300 ? dome(A.top.skull, 300, 165)(y) : table([[300, 165], [400, 160], [450, 148], [500, 128], [540, 96], [568, 50]])(y));
  add(loft(A.vault, skullWide, { rows: 64, ring: 56, nFront: 2.3, nBack: 2.2 }), BONE, 4);
  add(loft(A.face, table([[394, 96], [420, 140], [450, 152], [480, 150], [500, 118], [530, 84], [549, 70]]), { rows: 34, ring: 40, nFront: 2.6, nBack: 2 }), BONE, 4);
  for (const side of [-1, 1]) {                       // rims of the eye sockets
    const rim = add(new THREE.TorusGeometry(31, 1.3, 8, 32), BONE, 4);
    place(rim, 262, 431, side * 76); rim.rotation.y = Math.PI / 2 + side * 0.32; rim.scale.y = 0.95;
  }
  // The jaw: the side outline used twice, bent so the two halves meet at the chin.
  const jawWide = (x) => 118 * clamp((x - 214) / 190, 0, 1) ** 0.62;
  const jawShape = new THREE.Shape(A.mandible.map((p) => new THREE.Vector2(p[0], p[1])));
  for (const side of [-1, 1]) {
    const jaw = new THREE.ExtrudeGeometry(jawShape, { depth: 9, bevelEnabled: false, curveSegments: 1 });
    const p = jaw.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i), inset = p.getZ(i);
      p.setXYZ(i, x - A.pivot[0], A.pivot[1] - y, side * Math.max(0, jawWide(x) - inset));
    }
    jaw.computeVertexNormals();
    add(jaw, BONE, 4);
  }
  // Teeth: small rounded crowns set side by side along the curve of each dental arch.
  const archWide = (x) => 58 * clamp((x - 226) / 104, 0, 1) ** 0.5;
  const arch = []; let archLength = 0;
  for (let x = 226.5; x <= 331; x += 1.5) {
    const z = archWide(x);
    if (arch.length) archLength += Math.hypot(x - arch[arch.length - 1].x, z - arch[arch.length - 1].z);
    arch.push({ x, z, s: archLength });
  }
  const widths = A.teeth.map((t) => t.w), share = archLength / widths.reduce((a, b) => a + b, 0);
  let along = 0;
  A.teeth.forEach((t, k) => {
    const mid = along + (widths[k] * share) / 2; along += widths[k] * share;
    const i = Math.max(1, arch.findIndex((a) => a.s >= mid)), a = arch[i - 1], b = arch[i];
    for (const side of [-1, 1]) for (const up of [-1, 1]) {
      const tooth = add(new THREE.CylinderGeometry(up > 0 ? 0.5 : 0.38, up > 0 ? 0.38 : 0.5, 1, 12), DENSE, 4);   // widest at the biting edge
      tooth.scale.set(widths[k] * share - 0.8, t.crown - 1.5, 7.5);
      place(tooth, b.x + (up > 0 ? 2 : 0), 568 + up * (t.crown / 2), side * b.z);
      tooth.rotation.y = -side * Math.atan2(b.z - a.z, b.x - a.x);
    }
  });
  for (const v of A.spine) {
    const bone = new THREE.Group();
    bone.position.copy(at(v.x, v.y)); bone.rotation.z = -v.angle; model.add(bone);
    const part = (geometry, x, y, z) => { const m = new THREE.Mesh(geometry, BONE); m.position.set(x, y, z); m.renderOrder = 4; bone.add(m); return m; };
    part(new THREE.CylinderGeometry(v.w / 2, v.w / 2, v.h, 20), 0, 0, 0).scale.z = 1.25;
    part(new THREE.TorusGeometry(19, 4.5, 6, 20), v.w / 2 + 22, 0, 0).rotation.x = Math.PI / 2;
    const spine = part(new THREE.BoxGeometry(v.spinous, 9, 7), v.w / 2 + 40 + v.spinous / 2, -8, 0); spine.rotation.z = -0.22;
    for (const side of [-1, 1]) part(new THREE.BoxGeometry(14, 8, 24), 16, 0, side * 38);
  }
  const path = (poly, z = 0) => poly.filter((_, i) => i % 3 === 0 || i === poly.length - 1).map((p) => at(p[0], p[1], z));
  const windpipe = path(A.airway);
  add(tube(windpipe, windpipe.map(() => 11), 12), shell(0x86b4dc, 0.0, 0.3, 2.0), 5);

  // Brain: two halves of the cerebrum, the cerebellum, the brainstem and the cord.
  const brainWide = (y) => (y < 330 ? dome(A.top.brain, 330, 146)(y) : table([[330, 146], [420, 140], [460, 118], [488, 66]])(y));
  const CEREBRUM = tissue(0), CEREBELLUM = tissue(1), STEM = tissue(2);
  const halves = [-1, 1].map((side) => loft(A.cerebrum, brainWide, { rows: 72, ring: 44, side, gap: 5, nFront: 2.3, nBack: 2.3 }));
  for (const half of halves) add(half, CEREBRUM, 1);
  const lowerWide = (y) => 112 * Math.sqrt(Math.max(0, 1 - ((y - 497) / 47) ** 2));
  const lower = add(loft(A.cerebellum, lowerWide, { rows: 32, ring: 40, nFront: 2.2, nBack: 2.2 }), CEREBELLUM, 1).geometry;
  const stem = path(A.stem);
  add(tube(stem, stem.map((_, i) => 21 - 9 * (i / (stem.length - 1)) ** 2), 14), STEM, 1);
  const cord = path(A.cord);
  add(tube(cord, cord.map(() => 9), 10), shell(0x9cc8ee, 0.06, 0.4, 1.6), 5);

  // ---- arteries, on both sides -----------------------------------------------
  const brainReach = (x, y) => halves[1].userData.reach(x, y);
  const lowerReach = (x, y) => lower.userData.reach(x, y);
  const carotidOut = table([[436, 20], [470, 28], [500, 40], [540, 56], [590, 66], [700, 74], [905, 78]]);
  const vertebralOut = table([[532, 0], [556, 12], [580, 26], [640, 30], [905, 32]]);
  // Depth of one artery point, by the artery's role. `s` is the distance along it.
  function depth(role, x, y, s) {
    const ease = (len) => { const t = clamp(s / len, 0, 1); return t * t * (3 - 2 * t); };
    if (role === "carotid") return carotidOut(y);
    if (role === "vertebral") return vertebralOut(y);
    if (role === "inner") return 20 + (2 - 20) * ease(40);                       // runs between the two halves
    if (role === "innerBranch") return 2 + (brainReach(x, y) + 2.5 - 2) * ease(45);
    if (role === "outer") return 20 + (brainReach(x, y) + 2.5 - 20) * ease(60);  // comes out through the side fissure
    if (role === "rear") return (brainReach(x, y) + 2.5) * ease(70);
    if (role === "lower") return (lowerReach(x, y) + 2.5) * ease(60);
    return brainReach(x, y) + 2.5;                                               // "surface"
  }
  const VESSEL = (zone) => new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color() } }, vertexShader: VIEW_VERTEX,
    fragmentShader: `uniform vec3 uColor; varying vec3 vNormal; varying vec3 vView;
      void main() { float f = abs(dot(normalize(vNormal), normalize(vView))); gl_FragColor = vec4(uColor * (0.5 + 0.7 * f), 1.0); }`,
    side: THREE.DoubleSide, name: zone,
  });
  const vesselPaint = { front: VESSEL("front"), back: VESSEL("back") };
  const twigPaint = { front: new THREE.LineBasicMaterial({ transparent: true }), back: new THREE.LineBasicMaterial({ transparent: true }) };
  const dotPaint = {}, dotCloud = {};
  const round = document.createElement("canvas"); round.width = round.height = 32;      // a soft round dot
  const disc = round.getContext("2d"), glow = disc.createRadialGradient(16, 16, 0, 16, 16, 16);
  glow.addColorStop(0, "rgba(255,255,255,1)"); glow.addColorStop(0.55, "rgba(255,255,255,0.9)"); glow.addColorStop(1, "rgba(255,255,255,0)");
  disc.fillStyle = glow; disc.fillRect(0, 0, 32, 32);
  const dotMap = new THREE.CanvasTexture(round);
  const runs = [];                                   // one entry per artery per side
  const trunks = [];
  A.vessels.forEach((v, index) => {
    for (const side of [-1, 1]) {
      if (side < 0 && v.role === "vertebral") { /* the two join in the middle, so both are still drawn */ }
      const keep = v.poly.map((_, i) => i).filter((i) => i % 2 === 0 || i === v.poly.length - 1);
      const points = keep.map((i) => at(v.poly[i][0], v.poly[i][1], side * depth(v.role, v.poly[i][0], v.poly[i][1], v.d[i])));
      const along = keep.map((i) => v.d[i]);
      const radii = along.map((s) => v.widthAt(s) * 0.62);
      const geometry = tube(points, radii, v.width > 5 ? 10 : 6);
      add(geometry, vesselPaint[v.zone], 2);
      const run = { v, points, along };
      runs.push(run);
      if (index === 0) trunks.push({ geometry, along, radii });
    }
  });
  function pointOn(run, s, out) {
    const d = run.along;
    let lo = 0, hi = d.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (d[mid] <= s) lo = mid; else hi = mid; }
    return out.lerpVectors(run.points[lo], run.points[hi], clamp((s - d[lo]) / (d[hi] - d[lo] || 1), 0, 1));
  }
  // Fine branches: the flat view's branches, laid on the surface of each half.
  for (const zone of ["front", "back"]) {
    const segments = [];
    for (const side of [-1, 1]) for (const twig of A.twigs[zone]) {
      const lifted = twig.map(([x, y]) => {
        const reach = A.inCerebellum(x, y) ? lowerReach(x, y) + 1.6 : A.inCerebrum(x, y) ? brainReach(x, y) + 1.6 : 14;
        return at(x, y, side * reach);
      });
      for (let i = 1; i < lifted.length; i++) segments.push(lifted[i - 1], lifted[i]);
    }
    const lines = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(segments), twigPaint[zone]);
    lines.renderOrder = 2; model.add(lines);
    const count = runs.filter((r) => r.v.zone === zone).reduce((n, r) => n + Math.ceil(r.v.length / A.spacing) + 1, 0);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(count * 3), 3));
    dotPaint[zone] = new THREE.PointsMaterial({ size: 4, map: dotMap, sizeAttenuation: false, transparent: true, depthWrite: false });
    dotCloud[zone] = new THREE.Points(geometry, dotPaint[zone]);
    dotCloud[zone].renderOrder = 3; dotCloud[zone].frustumCulled = false; model.add(dotCloud[zone]);
  }
  // Rings that close on each carotid where it is compressed.
  const pinchAlong = A.pinchAlong, rings = [];
  for (const side of [-1, 1]) {
    const ring = add(new THREE.TorusGeometry(15, 2.2, 8, 28), new THREE.MeshBasicMaterial({ color: 0xe6f0fa }), 6);
    place(ring, A.pinch.x, A.pinch.y, side * carotidOut(A.pinch.y)); ring.rotation.x = Math.PI / 2; ring.visible = false;
    rings.push(ring);
  }

  // ---- eyes -------------------------------------------------------------------
  const lids = [];
  for (const side of [-1, 1]) {
    const eye = new THREE.Group(); eye.position.copy(at(277, 431, side * 76)); model.add(eye);
    // Only the front of the eye is drawn: the white, the iris and the pupil.
    const ball = new THREE.Mesh(new THREE.SphereGeometry(25, 28, 16, -1.25, 2.5, 0.35, 2.4), solid(0x7f93a6, THREE.FrontSide)); eye.add(ball);
    const iris = new THREE.Mesh(new THREE.CircleGeometry(9.5, 28), new THREE.MeshBasicMaterial({ color: 0x2a5578 }));
    iris.position.set(-25.3, 0, 0); iris.rotation.y = -Math.PI / 2; eye.add(iris);
    const pupil = new THREE.Mesh(new THREE.CircleGeometry(4.4, 20), new THREE.MeshBasicMaterial({ color: 0x03070b }));
    pupil.position.set(-25.6, 0, 0); pupil.rotation.y = -Math.PI / 2; eye.add(pupil);
    // Each lid is a patch of a slightly larger sphere whose two poles are the
    // corners of the eye, so the lids hinge there the way real ones do.
    const patch = (from, to) => {
      const g = new THREE.SphereGeometry(26.8, 16, 24, from, to - from, 0.2, Math.PI - 0.4); g.rotateX(Math.PI / 2);
      return new THREE.Mesh(g, solid(0x3a556e, THREE.FrontSide));
    };
    const upper = patch(-1.35, -0.32), lower = patch(0.3, 1.3);
    eye.add(upper); eye.add(lower); lids.push(upper);
  }

  // ---- labels (drawn over the 3D view) ----------------------------------------
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "overlay"); host.appendChild(svg);
  const labels = A.labels.map((l) => {
    const line = document.createElementNS(svg.namespaceURI, "line"), dot = document.createElementNS(svg.namespaceURI, "circle");
    const text = document.createElementNS(svg.namespaceURI, "text"), sub = document.createElementNS(svg.namespaceURI, "text");
    dot.setAttribute("r", 2.4); sub.setAttribute("class", "sub");
    for (const el of [line, dot, text, sub]) svg.appendChild(el);
    return { ...l, line, dot, text, sub };
  });
  const tag = document.createElement("div"); tag.className = "tag3d"; host.appendChild(tag);

  // ---- turning the head ---------------------------------------------------------
  let yaw = 0.55, pitch = 0.06, touched = false, dragging = null, width = 1, height = 1;
  const canvas = renderer.domElement;
  canvas.addEventListener("pointerdown", (e) => { dragging = { x: e.clientX, y: e.clientY, mouse: e.pointerType === "mouse" }; touched = true; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    yaw += (e.clientX - dragging.x) * 0.008;
    if (dragging.mouse) pitch = clamp(pitch + (e.clientY - dragging.y) * 0.006, -0.6, 0.6);
    dragging.x = e.clientX; dragging.y = e.clientY;
  });
  for (const type of ["pointerup", "pointercancel"]) canvas.addEventListener(type, () => { dragging = null; });
  canvas.addEventListener("keydown", (e) => {
    const step = { ArrowLeft: [-0.15, 0], ArrowRight: [0.15, 0], ArrowUp: [0, -0.1], ArrowDown: [0, 0.1] }[e.key];
    if (!step) return;
    yaw += step[0]; pitch = clamp(pitch + step[1], -0.6, 0.6); touched = true; e.preventDefault();
  });
  canvas.tabIndex = 0; canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "3D model of a head and neck showing blood flow to the brain. Drag, or use the arrow keys, to rotate.");

  function resize() {
    width = host.clientWidth || A.size[0]; height = (width * A.size[1]) / A.size[0];
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height, false);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    for (const zone in dotPaint) dotPaint[zone].size = clamp((4 * width) / 740, 2.4, 4);       // smaller dots on a small screen
  }

  const scratch = new V3(), colour = new THREE.Color();
  const blend = (a, b, f) => colour.setRGB((a[0] + (b[0] - a[0]) * f) / 255, (a[1] + (b[1] - a[1]) * f) / 255, (a[2] + (b[2] - a[2]) * f) / 255);
  let lastSqueeze = -1;
  // Draw one frame. `state` carries the model's numbers for this instant.
  function render(state, seconds) {
    if (!touched && !state.still) yaw = 0.55 + 0.22 * Math.sin(seconds * 0.35);
    model.rotation.set(pitch, yaw, 0, "XYZ");
    CEREBRUM.uniforms.uFront.value.setRGB(...state.frontColour.map((c) => c / 255));
    for (const m of [CEREBRUM, CEREBELLUM, STEM]) m.uniforms.uBack.value.setRGB(...state.backColour.map((c) => c / 255));
    for (const zone of ["front", "back"]) {
      const f = state.flow[zone], strength = Math.pow(f, 0.6);
      vesselPaint[zone].uniforms.uColor.value.copy(blend([88, 28, 38], [246, 58, 62], strength));
      twigPaint[zone].color.copy(blend([74, 26, 38], [255, 86, 80], strength)); twigPaint[zone].opacity = 0.2 + 0.75 * f;
      dotPaint[zone].color.setRGB(1, 0.91, 0.87); dotPaint[zone].opacity = 0.22 + 0.72 * f;
      const p = dotCloud[zone].geometry.attributes.position;
      let i = 0;
      for (const run of runs) {
        if (run.v.zone !== zone) continue;
        for (let s = run.v.phase % A.spacing; s < run.v.length && i < p.count; s += A.spacing, i++) {
          pointOn(run, s, scratch); p.setXYZ(i, scratch.x, scratch.y, scratch.z);
        }
      }
      for (; i < p.count; i++) p.setXYZ(i, 0, -9999, 0);
      p.needsUpdate = true;
    }
    if (state.squeeze !== lastSqueeze) {
      lastSqueeze = state.squeeze;
      for (const t of trunks) t.geometry.userData.shape(t.radii.map((r, i) => r * (1 - 0.86 * state.squeeze * Math.exp(-(((t.along[i] - pinchAlong) / 16) ** 2)))));
      for (const ring of rings) { ring.visible = state.squeeze > 0; const k = 1 - 0.55 * state.squeeze; ring.scale.set(k, k, 1); }
    }
    for (const lid of lids) lid.rotation.z = (1 - state.eye) * 0.66;            // swings forward and down to shut
    renderer.render(scene, camera);

    // Labels: each has a fixed spot at the edge and a line to its place on the head.
    const near = Math.cos(yaw) >= 0 ? 1 : -1;        // which side of the head faces the viewer
    model.updateMatrixWorld();
    for (const l of labels) {
      const show = !l.when || state[l.when];
      for (const el of [l.line, l.dot, l.text, l.sub]) el.style.display = show ? "" : "none";
      if (!show) continue;
      const anchor = at(l.at[0], l.at[1], (l.out || 0) * (l.mirror ? -near : near)).applyMatrix4(model.matrixWorld).project(camera);
      const ax = (anchor.x * 0.5 + 0.5) * width, ay = (-anchor.y * 0.5 + 0.5) * height;
      const sx = near > 0 ? l.spot[0] : 1 - l.spot[0];          // labels swap sides when the head faces the other way
      const right = sx > 0.5, lx = sx * width, ly = l.spot[1] * height;
      l.line.setAttribute("x1", ax); l.line.setAttribute("y1", ay); l.line.setAttribute("x2", lx + (right ? -6 : 6)); l.line.setAttribute("y2", ly - 5);
      l.dot.setAttribute("cx", ax); l.dot.setAttribute("cy", ay);
      const narrow = width < 520;
      for (const [el, textValue, dy] of [[l.text, narrow ? l.short : l.name, 0], [l.sub, narrow ? "" : l.note || "", 17]]) {
        el.textContent = textValue; el.setAttribute("x", lx); el.setAttribute("y", ly + dy); el.setAttribute("text-anchor", right ? "end" : "start");
      }
    }
    tag.style.display = state.frontOff ? "" : "none";
    if (state.frontOff) {
      const p = at(A.tagAt[0], A.tagAt[1], 0).applyMatrix4(model.matrixWorld).project(camera);
      tag.textContent = width < 520 ? "below threshold" : "below the model's threshold";
      tag.style.left = `${(p.x * 0.5 + 0.5) * 100}%`; tag.style.top = `${(-p.y * 0.5 + 0.5) * 100}%`;
    }
  }

  resize();
  return { render, resize, setView: (y, p) => { yaw = y; pitch = p; touched = true; } };
}

if (typeof module !== "undefined") module.exports = buildHead3D;
