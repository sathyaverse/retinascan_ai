/* ==========================================
   RetinaScan AI - Interactive 3D & Particle Engine
   ========================================== */

// --- Theme Toggle Setup ---
(function() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.add('light-theme');
  }
})();

window.toggleTheme = function() {
  if (document.body.classList.contains('light-theme')) {
    document.body.classList.remove('light-theme');
    localStorage.setItem('theme', 'dark');
  } else {
    document.body.classList.add('light-theme');
    localStorage.setItem('theme', 'light');
  }
};

document.addEventListener('DOMContentLoaded', function () {
  
  // --- 1. Auto-dismiss Flash Alerts ---
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'all 0.5s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      setTimeout(() => el.remove(), 500);
    }, 4500);
  });

  // --- 2. Interactive Neural Network Particle plexus Background ---
  const canvas = document.getElementById('neural-bg-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    let mouse = { x: null, y: null, radius: 150 };

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    window.addEventListener('mousemove', (e) => {
      mouse.x = e.x;
      mouse.y = e.y;
    });

    window.addEventListener('mouseout', () => {
      mouse.x = null;
      mouse.y = null;
    });

    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.45;
        this.vy = (Math.random() - 0.5) * 0.45;
        this.size = Math.random() * 2 + 1;
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > canvas.width) this.vx = -this.vx;
        if (this.y < 0 || this.y > canvas.height) this.vy = -this.vy;

        // Mouse reaction
        if (mouse.x != null && mouse.y != null) {
          let dx = this.x - mouse.x;
          let dy = this.y - mouse.y;
          let dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            let force = (mouse.radius - dist) / mouse.radius;
            this.x += (dx / dist) * force * 2;
            this.y += (dy / dist) * force * 2;
          }
        }
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 240, 255, 0.4)';
        ctx.fill();
      }
    }

    const initParticles = () => {
      particles = [];
      const count = Math.min(75, Math.floor((canvas.width * canvas.height) / 18000));
      for (let i = 0; i < count; i++) {
        particles.push(new Particle());
      }
    };
    initParticles();
    window.addEventListener('resize', initParticles);

    const animateParticles = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Update and draw particles
      particles.forEach(p => {
        p.update();
        p.draw();
      });

      // Connect particles with neural links
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          let dx = particles[i].x - particles[j].x;
          let dy = particles[i].y - particles[j].y;
          let dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 110) {
            let alpha = (110 - dist) / 110 * 0.12;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(animateParticles);
    };
    animateParticles();
  }

  // --- 3. Three.js 3D Retina Hologram Model ---
  // --- 3. Three.js 3D Retina Hologram Model & 2D HUD Fallback ---
  const retinaContainer = document.getElementById('canvas-3d-retina');
  if (retinaContainer) {
    const hasThree = (typeof THREE !== 'undefined');
    
    // Create the 2D overlay / fallback canvas
    const canvas2d = document.createElement('canvas');
    canvas2d.style.position = 'absolute';
    canvas2d.style.top = '0';
    canvas2d.style.left = '0';
    canvas2d.style.width = '100%';
    canvas2d.style.height = '100%';
    canvas2d.style.zIndex = '5';
    canvas2d.style.pointerEvents = 'none';
    retinaContainer.appendChild(canvas2d);
    
    const ctx2d = canvas2d.getContext('2d');
    
    const resize2d = () => {
      canvas2d.width = retinaContainer.clientWidth;
      canvas2d.height = retinaContainer.clientHeight;
    };
    resize2d();
    window.addEventListener('resize', resize2d);

    // Setup 3D if Three.js is loaded
    let renderer, scene, camera, hologramGroup, vesselGroup, retinaParticles, scanningRing1, scanningRing2;
    let targetRotationX = 0;
    let targetRotationY = 0;
    
    if (hasThree) {
      try {
        // Scene setup
        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(45, retinaContainer.clientWidth / retinaContainer.clientHeight, 0.1, 1000);
        camera.position.z = 8;

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(retinaContainer.clientWidth, retinaContainer.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        retinaContainer.appendChild(renderer.domElement);

        hologramGroup = new THREE.Group();
        scene.add(hologramGroup);

        // Glowing Retina Sphere (Point Cloud representation)
        const sphereGeometry = new THREE.SphereGeometry(2.2, 36, 36);
        const count = sphereGeometry.attributes.position.count;
        const colors = [];
        const sizes = [];

        for (let i = 0; i < count; i++) {
          const u = Math.random();
          if (u > 0.85) {
            colors.push(0.0, 0.94, 1.0); // Cyan
          } else if (u > 0.6) {
            colors.push(0.74, 0.0, 1.0); // Purple/Magenta
          } else {
            colors.push(0.1, 0.35, 0.8); // Darker Medical Blue
          }
          sizes.push(Math.random() * 0.06 + 0.02);
        }
        
        sphereGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
        
        const particleMaterial = new THREE.PointsMaterial({
          size: 0.075,
          vertexColors: true,
          transparent: true,
          opacity: 0.85,
          blending: THREE.AdditiveBlending
        });

        retinaParticles = new THREE.Points(sphereGeometry, particleMaterial);
        hologramGroup.add(retinaParticles);

        // Add Simulated Blood Vessels/Neural Network lines on surface
        const vesselMaterial = new THREE.LineBasicMaterial({
          color: 0xbd00ff,
          transparent: true,
          opacity: 0.35,
          blending: THREE.AdditiveBlending
        });
        
        vesselGroup = new THREE.Group();
        const numVessels = 12;
        for (let v = 0; v < numVessels; v++) {
          const points = [];
          const startAngle = Math.random() * Math.PI * 2;
          const phi = Math.acos(2 * Math.random() - 1);
          
          let currentTheta = startAngle;
          let currentPhi = phi;
          const radius = 2.22; // Slightly above shell

          for (let step = 0; step < 15; step++) {
            const x = radius * Math.sin(currentPhi) * Math.cos(currentTheta);
            const y = radius * Math.sin(currentPhi) * Math.sin(currentTheta);
            const z = radius * Math.cos(currentPhi);
            points.push(new THREE.Vector3(x, y, z));

            currentTheta += (Math.random() - 0.5) * 0.15;
            currentPhi += (Math.random() - 0.5) * 0.15;
          }
          
          const curve = new THREE.CatmullRomCurve3(points);
          const pointsArray = curve.getPoints(50);
          const vesselGeometry = new THREE.BufferGeometry().setFromPoints(pointsArray);
          const line = new THREE.Line(vesselGeometry, vesselMaterial);
          vesselGroup.add(line);
        }
        hologramGroup.add(vesselGroup);

        // Dynamic Holographic Scanning Dials (Outer Orbit Rings)
        const ringGeo = new THREE.RingGeometry(2.7, 2.73, 64);
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0x00f0ff,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.45,
          blending: THREE.AdditiveBlending
        });
        scanningRing1 = new THREE.Mesh(ringGeo, ringMat);
        scanningRing1.rotation.x = Math.PI / 2;
        hologramGroup.add(scanningRing1);

        const ringGeo2 = new THREE.RingGeometry(2.9, 2.91, 32);
        const ringMat2 = new THREE.MeshBasicMaterial({
          color: 0xff007a,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.25,
          blending: THREE.AdditiveBlending
        });
        scanningRing2 = new THREE.Mesh(ringGeo2, ringMat2);
        scanningRing2.rotation.y = Math.PI / 4;
        hologramGroup.add(scanningRing2);

        // Light source simulation
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0x00f0ff, 2, 20);
        pointLight.position.set(5, 5, 5);
        scene.add(pointLight);

        // Responsive sizing
        window.addEventListener('resize', () => {
          const width = retinaContainer.clientWidth;
          const height = retinaContainer.clientHeight;
          renderer.setSize(width, height);
          camera.aspect = width / height;
          camera.updateProjectionMatrix();
        });

        // Mouse movement interaction (parallax rotation)
        window.addEventListener('mousemove', (e) => {
          const rect = retinaContainer.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
            targetRotationY = (x / rect.width - 0.5) * 1.0;
            targetRotationX = (y / rect.height - 0.5) * 1.0;
          }
        });
      } catch (err) {
        console.error("Three.js initialization failed:", err);
      }
    }

    // --- 2D Retina Scanner Motion Graphics & HUD Animation ---
    // Pre-calculate vascular tree structures for 2D retina rendering
    const generateVascularTree = (cx, cy, r) => {
      const branches = [];
      const numMainBranches = 6;
      const odX = cx + r * 0.35; // Optic disc X
      const odY = cy - r * 0.15; // Optic disc Y
      
      for (let i = 0; i < numMainBranches; i++) {
        // Main arcades
        const angle = (i * Math.PI * 2 / numMainBranches) + (Math.random() - 0.5) * 0.3;
        const pts = [];
        pts.push({ x: odX, y: odY });
        
        let curX = odX;
        let curY = odY;
        let curDist = 0;
        const maxDist = r * (0.6 + Math.random() * 0.35);
        
        while (curDist < maxDist) {
          const stepSize = r * 0.12;
          const dev = (Math.random() - 0.5) * 0.8;
          // Curve arcades temporal-wise (left)
          let stepAngle = angle;
          if (i === 1 || i === 2) { // Upper temporal arcade
            stepAngle = Math.PI - 0.2 + (curDist / maxDist) * 1.0 + dev * 0.2;
          } else if (i === 4 || i === 5) { // Lower temporal arcade
            stepAngle = Math.PI + 0.2 - (curDist / maxDist) * 1.0 + dev * 0.2;
          } else {
            stepAngle = angle + dev * 0.35;
          }
          
          curX += Math.cos(stepAngle) * stepSize;
          curY += Math.sin(stepAngle) * stepSize;
          pts.push({ x: curX, y: curY });
          curDist += stepSize;
          
          // Side branch splits
          if (Math.random() < 0.3 && pts.length > 2) {
            const sideAngle = stepAngle + (Math.random() < 0.5 ? 0.75 : -0.75);
            const sidePts = [{ x: curX, y: curY }];
            let sX = curX;
            let sY = curY;
            for (let k = 0; k < 3; k++) {
              sX += Math.cos(sideAngle + (Math.random()-0.5)*0.2) * (stepSize * 0.7);
              sY += Math.sin(sideAngle + (Math.random()-0.5)*0.2) * (stepSize * 0.7);
              sidePts.push({ x: sX, y: sY });
            }
            branches.push({ points: sidePts, width: 0.8, flowSpeed: 0.05 + Math.random()*0.03, pulseOffset: Math.random()*10 });
          }
        }
        branches.push({ points: pts, width: 2.2 - (i % 2)*0.6, flowSpeed: 0.03 + Math.random()*0.02, pulseOffset: Math.random()*10 });
      }
      return { odX, odY, branches };
    };

    let vascularTree = null;
    
    // Virtual scans targets
    const scannerTargets = [
      { xOffset: -0.3, yOffset: -0.2, label: 'L_081 (MICROANEURYSM)', active: true, size: 22, color: '#ff007a' },
      { xOffset: -0.1, yOffset: 0.3, label: 'L_112 (HARD EXUDATE)', active: false, size: 28, color: '#ff7a00' },
      { xOffset: 0.25, yOffset: 0.25, label: 'SYS_TARGET (OPTIC DISC)', active: true, size: 40, color: '#00f0ff' }
    ];

    let startTime = Date.now();

    const animate = () => {
      requestAnimationFrame(animate);
      
      const time = (Date.now() - startTime) * 0.001;
      
      // Update Three.js if active
      if (hasThree && renderer) {
        try {
          hologramGroup.rotation.y += 0.003;
          vesselGroup.rotation.y += 0.002;
          retinaParticles.rotation.y += 0.0015;
          
          scanningRing1.rotation.z = time * 0.25;
          scanningRing2.rotation.z = -time * 0.15;
          
          const pulse = 1 + Math.sin(time * 2) * 0.03;
          scanningRing1.scale.set(pulse, pulse, 1);

          hologramGroup.rotation.y += (targetRotationY - hologramGroup.rotation.y) * 0.05;
          hologramGroup.rotation.x += (targetRotationX - hologramGroup.rotation.x) * 0.05;

          renderer.render(scene, camera);
        } catch (err) {}
      }

      // --- 2D HUD Canvas Animation ---
      const w = canvas2d.width;
      const h = canvas2d.height;
      if (w === 0 || h === 0) return;

      ctx2d.clearRect(0, 0, w, h);
      
      const cx = w / 2;
      const cy = h / 2;
      const r = Math.min(w, h) * 0.4;
      
      // Generate paths once dimensions are resolved
      if (!vascularTree) {
        vascularTree = generateVascularTree(cx, cy, r);
      }

      // --- Mode A: Full 2D Retina Draw (Three.js failed/missing) ---
      if (!hasThree) {
        // 1. Draw fundus circular boundary
        ctx2d.beginPath();
        ctx2d.arc(cx, cy, r, 0, Math.PI * 2);
        const fundusGrad = ctx2d.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
        fundusGrad.addColorStop(0, 'rgba(10, 15, 36, 0.8)');
        fundusGrad.addColorStop(0.7, 'rgba(6, 9, 21, 0.9)');
        fundusGrad.addColorStop(1, 'rgba(0, 3, 10, 0.95)');
        ctx2d.fillStyle = fundusGrad;
        ctx2d.fill();
        
        ctx2d.strokeStyle = 'rgba(0, 240, 255, 0.15)';
        ctx2d.lineWidth = 1.5;
        ctx2d.stroke();

        // 2. Draw Optic Disc (yellow glowing circle)
        const { odX, odY } = vascularTree;
        ctx2d.beginPath();
        ctx2d.arc(odX, odY, r * 0.12, 0, Math.PI * 2);
        const odGrad = ctx2d.createRadialGradient(odX, odY, 0, odX, odY, r * 0.12);
        odGrad.addColorStop(0, 'rgba(255, 235, 120, 0.65)');
        odGrad.addColorStop(0.6, 'rgba(255, 120, 0, 0.3)');
        odGrad.addColorStop(1, 'rgba(255, 120, 0, 0)');
        ctx2d.fillStyle = odGrad;
        ctx2d.fill();

        // 3. Draw Macula (dark central zone)
        const maculaX = cx - r * 0.25;
        const maculaY = cy + r * 0.05;
        ctx2d.beginPath();
        ctx2d.arc(maculaX, maculaY, r * 0.16, 0, Math.PI * 2);
        const macGrad = ctx2d.createRadialGradient(maculaX, maculaY, 0, maculaX, maculaY, r * 0.16);
        macGrad.addColorStop(0, 'rgba(180, 40, 40, 0.15)');
        macGrad.addColorStop(0.7, 'rgba(120, 30, 30, 0.08)');
        macGrad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx2d.fillStyle = macGrad;
        ctx2d.fill();

        // Macula target crosshair
        ctx2d.strokeStyle = 'rgba(180, 40, 40, 0.25)';
        ctx2d.lineWidth = 0.5;
        ctx2d.stroke();

        // 4. Draw Blood Vessel Branches
        vascularTree.branches.forEach(b => {
          ctx2d.beginPath();
          ctx2d.moveTo(b.points[0].x, b.points[0].y);
          for (let i = 1; i < b.points.length; i++) {
            // Bezier-like smooth spline
            const prev = b.points[i-1];
            const curr = b.points[i];
            const midX = (prev.x + curr.x) / 2;
            const midY = (prev.y + curr.y) / 2;
            ctx2d.quadraticCurveTo(prev.x, prev.y, midX, midY);
          }
          ctx2d.strokeStyle = 'rgba(255, 0, 102, 0.35)'; // Reddish blood vessels
          ctx2d.lineWidth = b.width;
          ctx2d.lineCap = 'round';
          ctx2d.stroke();
          
          // Flowing blood pulses (small light packets traversing paths)
          const pulseCount = 2;
          for (let p = 0; p < pulseCount; p++) {
            const progress = ((time * b.flowSpeed) + (p / pulseCount) + b.pulseOffset) % 1.0;
            const floatIdx = progress * (b.points.length - 1);
            const idx = Math.floor(floatIdx);
            const nextIdx = Math.min(idx + 1, b.points.length - 1);
            const ratio = floatIdx - idx;
            
            if (idx < b.points.length) {
              const pt = b.points[idx];
              const nPt = b.points[nextIdx];
              const px = pt.x + (nPt.x - pt.x) * ratio;
              const py = pt.y + (nPt.y - pt.y) * ratio;
              
              ctx2d.beginPath();
              ctx2d.arc(px, py, b.width * 0.9 + 0.3, 0, Math.PI * 2);
              ctx2d.fillStyle = 'rgba(0, 240, 255, 0.75)'; // Glowing cyan pulse
              ctx2d.shadowColor = '#00f0ff';
              ctx2d.shadowBlur = 4;
              ctx2d.fill();
              ctx2d.shadowBlur = 0; // Reset
            }
          }
        });
      }

      // --- Mode B: HUD Overlay Graphics (Runs in both full and 3D overlay) ---
      // 1. Rotating sci-fi grid rings
      ctx2d.save();
      ctx2d.translate(cx, cy);
      
      // Outer ring
      ctx2d.beginPath();
      ctx2d.arc(0, 0, r * 1.08, 0, Math.PI * 2);
      ctx2d.strokeStyle = 'rgba(0, 240, 255, 0.2)';
      ctx2d.lineWidth = 1;
      ctx2d.setLineDash([4, 15]);
      ctx2d.stroke();
      
      // Degree ticks on outer ring
      ctx2d.rotate(time * 0.08);
      ctx2d.beginPath();
      ctx2d.arc(0, 0, r * 1.11, 0, Math.PI * 2);
      ctx2d.strokeStyle = 'rgba(189, 0, 255, 0.25)';
      ctx2d.lineWidth = 2.5;
      ctx2d.setLineDash([2, 50]);
      ctx2d.stroke();
      
      // Secondary telemetry ring
      ctx2d.rotate(-time * 0.15);
      ctx2d.beginPath();
      ctx2d.arc(0, 0, r * 0.92, 0, Math.PI * 2);
      ctx2d.strokeStyle = 'rgba(0, 240, 255, 0.12)';
      ctx2d.setLineDash([12, 40, 2, 40]);
      ctx2d.stroke();

      ctx2d.restore();
      
      // 2. Horizontal scanning laser bar
      const scanPeriod = 5.0; // 5 seconds sweep
      const sweepY = cy + Math.sin(time * (Math.PI * 2 / scanPeriod)) * (r * 0.95);
      
      // Draw glowing laser sweep gradient
      const laserGrad = ctx2d.createLinearGradient(0, sweepY - 15, 0, sweepY + 15);
      laserGrad.addColorStop(0, 'rgba(0, 240, 255, 0.0)');
      laserGrad.addColorStop(0.5, 'rgba(0, 240, 255, 0.25)'); // Peak glow
      laserGrad.addColorStop(1, 'rgba(0, 240, 255, 0.0)');
      
      ctx2d.fillStyle = laserGrad;
      ctx2d.fillRect(cx - r * 0.95, sweepY - 15, r * 1.9, 30);
      
      // Laser core line
      ctx2d.beginPath();
      ctx2d.moveTo(cx - r * 0.95, sweepY);
      ctx2d.lineTo(cx + r * 0.95, sweepY);
      ctx2d.strokeStyle = 'rgba(0, 240, 255, 0.65)';
      ctx2d.lineWidth = 1.2;
      ctx2d.stroke();

      // Scan Sweep Intersections (glowing nodes flickering on line)
      if (Math.abs(Math.sin(time * 3)) > 0.4) {
        ctx2d.beginPath();
        ctx2d.arc(cx + Math.cos(time*2.5)*r*0.6, sweepY, 3, 0, Math.PI*2);
        ctx2d.fillStyle = '#00f0ff';
        ctx2d.fill();
      }

      // 3. Draw diagnostic targets (flickering tracking boxes)
      scannerTargets.forEach((t, i) => {
        const tx = cx + t.xOffset * r * 2;
        const ty = cy + t.yOffset * r * 2;
        
        // Target bracket active cycle (periodic flicker)
        const isFlickerActive = (Math.floor(time * 2 + i) % 4 !== 0);
        if (isFlickerActive) {
          ctx2d.strokeStyle = t.color;
          ctx2d.lineWidth = 1.2;
          
          // Draw corners of targeting box
          const size = t.size + Math.sin(time * 6) * 1.5;
          const half = size / 2;
          const cLen = 6; // Corner line length
          
          // Top Left
          ctx2d.beginPath();
          ctx2d.moveTo(tx - half, ty - half + cLen);
          ctx2d.lineTo(tx - half, ty - half);
          ctx2d.lineTo(tx - half + cLen, ty - half);
          ctx2d.stroke();
          
          // Top Right
          ctx2d.beginPath();
          ctx2d.moveTo(tx + half, ty - half + cLen);
          ctx2d.lineTo(tx + half, ty - half);
          ctx2d.lineTo(tx + half - cLen, ty - half);
          ctx2d.stroke();

          // Bottom Left
          ctx2d.beginPath();
          ctx2d.moveTo(tx - half, ty + half - cLen);
          ctx2d.lineTo(tx - half, ty + half);
          ctx2d.lineTo(tx - half + cLen, ty + half);
          ctx2d.stroke();

          // Bottom Right
          ctx2d.beginPath();
          ctx2d.moveTo(tx + half, ty + half - cLen);
          ctx2d.lineTo(tx + half, ty + half);
          ctx2d.lineTo(tx + half - cLen, ty + half);
          ctx2d.stroke();
          
          // Draw target center dot
          ctx2d.beginPath();
          ctx2d.arc(tx, ty, 2, 0, Math.PI*2);
          ctx2d.fillStyle = t.color;
          ctx2d.fill();

          // Diagnostic text labels
          ctx2d.fillStyle = 'rgba(255,255,255,0.7)';
          ctx2d.font = '500 8px "Orbitron", "Space Grotesk", monospace';
          ctx2d.fillText(t.label, tx + half + 4, ty + 2);
          ctx2d.fillText(`POS_XY: ${Math.floor(tx)},${Math.floor(ty)}`, tx + half + 4, ty + 11);
        }
      });

      // 4. Futuristic HUD HUD telemetry dashboard stats (top left & bottom right corners)
      ctx2d.fillStyle = 'rgba(0, 240, 255, 0.45)';
      ctx2d.font = '600 9px "Orbitron", monospace';
      
      // Top Left Text
      ctx2d.fillText(`RETINA_SCAN: ACTIVE`, cx - r * 0.9, cy - r * 0.8);
      ctx2d.fillText(`RESOLUTION: 2048 x 2048`, cx - r * 0.9, cy - r * 0.73);
      
      // Bottom Right Text
      ctx2d.fillStyle = 'rgba(189, 0, 255, 0.5)';
      ctx2d.fillText(`EHR_SYNC: INTEROPERABLE (FHIR)`, cx + r * 0.35, cy + r * 0.85);
      
      // Scanning sweeping effect text
      ctx2d.fillStyle = 'rgba(0, 240, 255, 0.65)';
      const scanPercent = Math.floor((time * 20) % 100);
      ctx2d.fillText(`AI_ANALYSIS: ${scanPercent}% SECURED`, cx - r * 0.9, cy + r * 0.85);
    };
    animate();
  }

  // --- 4. Card Parallax Mouse-Tilt Physics ---
  const tiltCards = document.querySelectorAll('.tilt-card');
  tiltCards.forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      
      const tiltX = (y / (rect.height / 2)) * -8; // Max tilt angle
      const tiltY = (x / (rect.width / 2)) * 8;
      
      card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
  });

  // --- 5. Interactive Stat Counters ---
  const counters = document.querySelectorAll('.counter-val');
  if (counters.length > 0) {
    const runCounter = (el) => {
      const target = parseFloat(el.getAttribute('data-target'));
      const suffix = el.getAttribute('data-suffix') || '';
      let current = 0;
      const step = target / 60; // 60 frames/sec animation
      
      const updateValue = () => {
        current += step;
        if (current >= target) {
          el.innerText = target.toLocaleString() + suffix;
        } else {
          el.innerText = Math.floor(current).toLocaleString() + suffix;
          requestAnimationFrame(updateValue);
        }
      };
      updateValue();
    };

    // Use IntersectionObserver to start counters when scrolled into view
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          runCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.6 });

    counters.forEach(c => observer.observe(c));
  }
});
