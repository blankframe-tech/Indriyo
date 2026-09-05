/**
 * Indriyo (ইন্দ্রিয়) - Interactive In-Browser ADAS Live Simulator
 * Real-time HTML5 Canvas engine with Web Audio API sound synthesizer.
 */

class AdasSimulator {
  constructor(canvasId, frameId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.frameEl = document.getElementById(frameId);

    // Audio Context for synthetic chimes
    this.audioCtx = null;
    this.soundEnabled = false;
    this.lastSoundTime = 0;

    // Simulation State
    this.bikeSpeedKmh = 60.0;
    this.scenario = 'tailgater';
    this.showGrid = true;
    this.showBoxes = true;
    this.isMirrored = true;

    // Road animation phase
    this.roadPhase = 0;
    this.lastFrameTime = performance.now();
    this.fps = 60;
    this.flashState = false;
    this.lastFlashToggle = performance.now();

    // Vehicles in scenario
    this.vehicles = [];
    this.initScenario(this.scenario);

    // Resize canvas
    this.handleResize();
    window.addEventListener('resize', () => this.handleResize());

    // Start render loop
    requestAnimationFrame((t) => this.loop(t));
  }

  handleResize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = 480;
  }

  initAudio() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  playBeep(freq1, dur1, gap, freq2, dur2) {
    if (!this.soundEnabled || !this.audioCtx) return;
    try {
      const now = this.audioCtx.currentTime;
      // Tone 1
      const osc1 = this.audioCtx.createOscillator();
      const gain1 = this.audioCtx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(freq1, now);
      gain1.gain.setValueAtTime(0.15, now);
      gain1.gain.exponentialRampToValueAtTime(0.01, now + dur1);
      osc1.connect(gain1);
      gain1.connect(this.audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + dur1);

      // Tone 2
      if (freq2) {
        const osc2 = this.audioCtx.createOscillator();
        const gain2 = this.audioCtx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(freq2, now + dur1 + gap);
        gain2.gain.setValueAtTime(0.2, now + dur1 + gap);
        gain2.gain.exponentialRampToValueAtTime(0.01, now + dur1 + gap + dur2);
        osc2.connect(gain2);
        gain2.connect(this.audioCtx.destination);
        osc2.start(now + dur1 + gap);
        osc2.stop(now + dur1 + gap + dur2);
      }
    } catch (e) {
      console.warn("WebAudio err:", e);
    }
  }

  initScenario(name) {
    this.scenario = name;
    this.vehicles = [];

    if (name === 'tailgater') {
      this.vehicles.push({
        type: 'car',
        label: 'Sedan',
        color: '#dc3545',
        dist: 42.0,
        relSpeed: 32.0,
        latOffset: 0.0,
        initialDist: 45.0,
        behavior: 'tailgater'
      });
    } else if (name === 'blindspot') {
      this.vehicles.push({
        type: 'car',
        label: 'SUV',
        color: '#ffc107',
        dist: 12.0,
        relSpeed: 8.0,
        latOffset: -0.65,
        initialDist: 14.0,
        behavior: 'hover_blindspot'
      });
    } else if (name === 'dual_overtake') {
      this.vehicles.push({
        type: 'car',
        label: 'Sport Sedan',
        color: '#0d6efd',
        dist: 35.0,
        relSpeed: 24.0,
        latOffset: 0.62,
        initialDist: 38.0,
        behavior: 'overtake'
      });
      this.vehicles.push({
        type: 'motorcycle',
        label: 'Yamaha R15',
        color: '#198754',
        dist: 22.0,
        relSpeed: 16.0,
        latOffset: -0.58,
        initialDist: 26.0,
        behavior: 'overtake'
      });
    } else { // dhaka_traffic
      this.vehicles.push({
        type: 'bus',
        label: 'Local Bus',
        color: '#17a2b8',
        dist: 28.0,
        relSpeed: 14.0,
        latOffset: 0.1,
        initialDist: 32.0,
        behavior: 'overtake'
      });
      this.vehicles.push({
        type: 'motorcycle',
        label: 'Bike',
        color: '#fd7e14',
        dist: 8.0,
        relSpeed: 5.0,
        latOffset: -0.68,
        initialDist: 10.0,
        behavior: 'hover_blindspot'
      });
    }
  }

  setSpeed(speedKmh) {
    this.bikeSpeedKmh = speedKmh;
  }

  toggleSound() {
    this.initAudio();
    this.soundEnabled = !this.soundEnabled;
    return this.soundEnabled;
  }

  toggleGrid() {
    this.showGrid = !this.showGrid;
    return this.showGrid;
  }

  toggleBoxes() {
    this.showBoxes = !this.showBoxes;
    return this.showBoxes;
  }

  loop(timestamp) {
    const dt = Math.min(0.1, (timestamp - this.lastFrameTime) / 1000.0);
    this.lastFrameTime = timestamp;
    this.fps = Math.round(1.0 / Math.max(0.001, dt));

    if (timestamp - this.lastFlashToggle > 160) {
      this.flashState = !this.flashState;
      this.lastFlashToggle = timestamp;
    }

    this.update(dt);
    this.render();

    requestAnimationFrame((t) => this.loop(t));
  }

  update(dt) {
    // Road speed motion
    const speedFactor = Math.max(0.1, this.bikeSpeedKmh / 50.0);
    this.roadPhase = (this.roadPhase + dt * speedFactor * 4.5) % 1.0;

    // Update vehicle positions
    for (let v of this.vehicles) {
      // Speed adjustments
      let effectiveRelSpeed = v.relSpeed;
      if (this.bikeSpeedKmh === 0) {
        effectiveRelSpeed = Math.max(20.0, v.relSpeed + 15.0);
      }

      const speedMs = effectiveRelSpeed / 3.6;
      v.dist -= speedMs * dt;

      if (v.behavior === 'tailgater') {
        if (v.dist < 2.5) v.dist = v.initialDist;
      } else if (v.behavior === 'hover_blindspot') {
        if (v.dist < 4.2) v.relSpeed = -2.5;
        else if (v.dist > 7.5) v.relSpeed = 3.5;
      } else if (v.behavior === 'overtake') {
        if (v.dist < 2.5) v.dist = v.initialDist;
      }
    }
  }

  render() {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;

    ctx.clearRect(0, 0, w, h);

    // 1. Horizon & Sky / Dusk Gradient
    const vanishY = h * 0.38;
    const skyGrad = ctx.createLinearGradient(0, 0, 0, vanishY);
    skyGrad.addColorStop(0, '#0a0d14');
    skyGrad.addColorStop(0.7, '#151b29');
    skyGrad.addColorStop(1, '#2c2226');
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, w, vanishY);

    // City silhouettes in distance
    ctx.fillStyle = '#06090e';
    for (let i = 0; i < 18; i++) {
      const bx = (i * 70 + (this.roadPhase * 20)) % (w + 60) - 30;
      const bw = 35 + (i % 5) * 12;
      const bh = 25 + (i % 7) * 18;
      ctx.fillRect(bx, vanishY - bh, bw, bh);
    }

    // 2. Road plane
    const roadGrad = ctx.createLinearGradient(0, vanishY, 0, h);
    roadGrad.addColorStop(0, '#15171d');
    roadGrad.addColorStop(1, '#0e1014');
    ctx.fillStyle = roadGrad;
    ctx.fillRect(0, vanishY, w, h - vanishY);

    // 3. Dynamic Animated Lane Lines (Rear perspective)
    ctx.strokeStyle = '#6b7280';
    ctx.lineWidth = 2;
    const numDashes = 10;
    for (let i = 0; i < numDashes; i++) {
      const relPos = ((i / numDashes) + this.roadPhase) % 1.0;
      const curY = vanishY + (h - vanishY) * Math.pow(relPos, 1.8);
      const nextY = vanishY + (h - vanishY) * Math.pow(Math.min(1.0, relPos + 0.05), 1.8);
      const lw = Math.max(1.5, relPos * 8);

      ctx.lineWidth = lw;
      // Left lane
      const lx = (w * 0.5) - (w * 0.32) * relPos;
      ctx.beginPath();
      ctx.moveTo(lx, curY);
      ctx.lineTo(lx, nextY);
      ctx.stroke();

      // Right lane
      const rx = (w * 0.5) + (w * 0.32) * relPos;
      ctx.beginPath();
      ctx.moveTo(rx, curY);
      ctx.lineTo(rx, nextY);
      ctx.stroke();
    }

    // 4. Subtle Blind Spot Guidelines
    if (this.showGrid) {
      ctx.save();
      ctx.setLineDash([6, 8]);
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.2)';
      ctx.lineWidth = 1;

      const leftBoundary = w * 0.35;
      const rightBoundary = w * 0.65;
      ctx.beginPath();
      ctx.moveTo(leftBoundary, vanishY);
      ctx.lineTo(leftBoundary, h);
      ctx.moveTo(rightBoundary, vanishY);
      ctx.lineTo(rightBoundary, h);
      ctx.stroke();

      // Zone tags
      ctx.font = '10px monospace';
      ctx.fillStyle = 'rgba(0, 240, 255, 0.4)';
      ctx.fillText('◀ LEFT BLIND SPOT', 20, vanishY + 25);
      ctx.fillText('RIGHT BLIND SPOT ▶', w - 150, vanishY + 25);
      ctx.restore();
    }

    // 5. Threat Assessment & Vehicle Rendering
    let highestThreat = 0; // 0: clear, 1: monitoring, 2: warning, 3: critical
    let leftBsActive = false;
    let rightBsActive = false;
    let minTtc = 99;

    const focal = h * 0.9;
    const sortedVehicles = [...this.vehicles].sort((a, b) => b.dist - a.dist);

    for (let v of sortedVehicles) {
      if (v.dist < 0.5) continue;

      const scale = focal / v.dist;
      const nominalW = v.type === 'motorcycle' ? 0.9 : (v.type === 'bus' ? 2.4 : 1.8);
      const nominalH = v.type === 'motorcycle' ? 1.3 : (v.type === 'bus' ? 2.8 : 1.4);
      const boxW = Math.max(16, nominalW * scale);
      const boxH = Math.max(16, nominalH * scale);

      // Camera horizontal position (mirrored for rearview mirror)
      const mirrorMultiplier = this.isMirrored ? -1 : 1;
      const centerX = (w * 0.5) + (v.latOffset * mirrorMultiplier * (w * 0.45) * (1.0 - (v.dist / 70.0)));
      const centerY = vanishY + (h - vanishY) * (1.0 / (1.0 + v.dist * 0.12));

      const x1 = Math.max(0, centerX - boxW / 2);
      const y1 = Math.max(vanishY, centerY - boxH);
      const x2 = Math.min(w, centerX + boxW / 2);
      const y2 = Math.min(h - 10, centerY);

      // Render 3D car body
      ctx.fillStyle = v.color;
      ctx.fillRect(x1, y1 + boxH * 0.35, boxW, boxH * 0.65);

      // Cabin / windshield
      ctx.fillStyle = '#11151c';
      ctx.fillRect(x1 + boxW * 0.15, y1, boxW * 0.7, boxH * 0.38);

      // Headlights with dynamic flare
      const hlY = y2 - boxH * 0.25;
      const hlRadius = Math.max(2, boxW * 0.08);

      ctx.fillStyle = '#fffdf0';
      ctx.beginPath();
      ctx.arc(x1 + boxW * 0.2, hlY, hlRadius, 0, Math.PI * 2);
      ctx.arc(x2 - boxW * 0.2, hlY, hlRadius, 0, Math.PI * 2);
      ctx.fill();

      // Headlight glow
      if (boxW > 35) {
        ctx.fillStyle = 'rgba(255, 240, 200, 0.25)';
        ctx.beginPath();
        ctx.arc(x1 + boxW * 0.2, hlY, hlRadius * 3, 0, Math.PI * 2);
        ctx.arc(x2 - boxW * 0.2, hlY, hlRadius * 3, 0, Math.PI * 2);
        ctx.fill();
      }

      // Grille
      ctx.fillStyle = '#0a0d12';
      ctx.fillRect(x1 + boxW * 0.28, hlY - 2, boxW * 0.44, Math.max(4, boxH * 0.18));

      // Calculate TTC and Zone
      const relSpeedKmh = this.bikeSpeedKmh === 0 ? v.relSpeed + 20 : v.relSpeed;
      const relSpeedMs = Math.max(0.1, relSpeedKmh / 3.6);
      const ttc = v.dist / relSpeedMs;

      const normX = centerX / w;
      const isLeft = normX <= 0.35;
      const isRight = normX >= 0.65;

      let threat = 0;
      let threatDesc = 'Following';

      // Adaptive rule: bike stopped at red light
      if (this.bikeSpeedKmh < 10) {
        if (ttc < 2.2 && v.dist < 30) {
          threat = 3;
          threatDesc = 'FAST REAR THREAT (STOPPED)';
        } else if (v.dist < 8) {
          threat = 2;
          threatDesc = 'CLOSE PROXIMITY';
        }
      } else {
        if (ttc < 1.8 && relSpeedKmh > 10) {
          threat = 3;
          threatDesc = `CRITICAL! TTC: ${ttc.toFixed(1)}s`;
        } else if ((isLeft || isRight) && v.dist < 8.0) {
          threat = 2;
          threatDesc = 'BLIND SPOT';
        } else if (ttc < 3.2 && relSpeedKmh > 8) {
          threat = 2;
          threatDesc = `APPROACHING (+${relSpeedKmh.toFixed(0)} km/h)`;
        } else {
          threat = 1;
        }
      }

      if (isLeft && threat >= 2) leftBsActive = true;
      if (isRight && threat >= 2) rightBsActive = true;
      if (threat > highestThreat) highestThreat = threat;
      if (ttc < minTtc && relSpeedKmh > 5) minTtc = ttc;

      // Draw Corner Brackets HUD
      if (this.showBoxes) {
        this.drawTargetHud(ctx, x1, y1, x2, y2, v, ttc, threat, threatDesc);
      }
    }

    // 6. Sound Synthesizer Trigger
    const nowTs = performance.now();
    if (highestThreat === 3) {
      if (nowTs - this.lastSoundTime > 400) {
        this.playBeep(1600, 0.08, 0.03, 1950, 0.08);
        this.lastSoundTime = nowTs;
      }
    } else if (highestThreat === 2) {
      if (nowTs - this.lastSoundTime > 1800) {
        this.playBeep(880, 0.1, 0.05, 1174, 0.12);
        this.lastSoundTime = nowTs;
      }
    }

    // 7. Render Peripheral Awareness Perimeter Borders (PRD Core Feature)
    this.drawPeripheralBorders(ctx, w, h, highestThreat, leftBsActive, rightBsActive);

    // 8. Render Cockpit Top Header
    this.drawTopHeader(ctx, w, h, highestThreat);

    // 9. Update Outer CSS Display Frame Alert Classes
    if (this.frameEl) {
      this.frameEl.classList.remove('alert-warning', 'alert-critical');
      if (highestThreat === 3) {
        this.frameEl.classList.add('alert-critical');
      } else if (highestThreat === 2) {
        this.frameEl.classList.add('alert-warning');
      }
    }
  }

  drawTargetHud(ctx, x1, y1, x2, y2, v, ttc, threat, threatDesc) {
    let color = '#30d158'; // Clear green
    let thickness = 1.5;

    if (threat === 3) {
      color = this.flashState ? '#ff2a4b' : '#ff8598';
      thickness = 3;
    } else if (threat === 2) {
      color = '#ff9d00'; // Amber
      thickness = 2;
    } else if (threat === 1) {
      color = '#00f0ff'; // Cyan
    }

    const bw = x2 - x1;
    const bh = y2 - y1;
    const cornerLen = Math.max(6, Math.min(22, bw * 0.25));

    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = thickness;

    // Corner brackets
    // Top-left
    ctx.beginPath();
    ctx.moveTo(x1, y1 + cornerLen);
    ctx.lineTo(x1, y1);
    ctx.lineTo(x1 + cornerLen, y1);
    // Top-right
    ctx.moveTo(x2 - cornerLen, y1);
    ctx.lineTo(x2, y1);
    ctx.lineTo(x2, y1 + cornerLen);
    // Bottom-left
    ctx.beginPath();
    ctx.moveTo(x1, y2 - cornerLen);
    ctx.lineTo(x1, y2);
    ctx.lineTo(x1 + cornerLen, y2);
    // Bottom-right
    ctx.moveTo(x2 - cornerLen, y2);
    ctx.lineTo(x2, y2);
    ctx.lineTo(x2, y2 - cornerLen);
    ctx.stroke();

    // Target pill badge
    const badgeText = `${v.label.toUpperCase()} | ${v.dist.toFixed(1)}m | ${threatDesc}`;
    ctx.font = 'bold 11px monospace';
    const textWidth = ctx.measureText(badgeText).width;

    const badgeY = Math.max(20, y1 - 8);
    ctx.fillStyle = 'rgba(6, 9, 14, 0.85)';
    ctx.fillRect(x1, badgeY - 14, textWidth + 12, 18);
    ctx.strokeStyle = color;
    ctx.strokeRect(x1, badgeY - 14, textWidth + 12, 18);

    ctx.fillStyle = color;
    ctx.fillText(badgeText, x1 + 6, badgeY - 1);
    ctx.restore();
  }

  drawPeripheralBorders(ctx, w, h, highestThreat, leftActive, rightActive) {
    const borderThickness = 12;

    if (highestThreat === 3) {
      // Rapid flashing red perimeter
      if (this.flashState) {
        ctx.strokeStyle = '#ff2a4b';
        ctx.lineWidth = borderThickness;
        ctx.strokeRect(0, 0, w, h);

        // Emergency Banner in center
        ctx.save();
        ctx.fillStyle = 'rgba(255, 42, 75, 0.9)';
        ctx.fillRect(w * 0.5 - 160, 48, 320, 36);
        ctx.font = 'bold 14px sans-serif';
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.fillText('⚠️ COLLISION HAZARD - EVADE', w * 0.5, 71);
        ctx.restore();
      }
    } else if (highestThreat === 2) {
      // Solid amber border on active threat side
      ctx.lineWidth = borderThickness;
      ctx.strokeStyle = '#ff9d00';

      if (leftActive) {
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, h);
        ctx.lineTo(w * 0.35, h);
        ctx.stroke();
      }
      if (rightActive) {
        ctx.beginPath();
        ctx.moveTo(w, 0);
        ctx.lineTo(w, h);
        ctx.lineTo(w - (w * 0.35), h);
        ctx.stroke();
      }
      if (!leftActive && !rightActive) {
        ctx.strokeRect(0, 0, w, h);
      }
    } else {
      // Subtle top/bottom safe lines
      ctx.strokeStyle = 'rgba(48, 209, 88, 0.35)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, 2);
      ctx.lineTo(w, 2);
      ctx.moveTo(0, h - 2);
      ctx.lineTo(w, h - 2);
      ctx.stroke();
    }
  }

  drawTopHeader(ctx, w, h, highestThreat) {
    ctx.save();
    // Glass banner
    ctx.fillStyle = 'rgba(6, 9, 14, 0.85)';
    ctx.fillRect(0, 0, w, 40);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.beginPath();
    ctx.moveTo(0, 40);
    ctx.lineTo(w, 40);
    ctx.stroke();

    // Brand
    ctx.font = 'bold 13px sans-serif';
    ctx.fillStyle = '#fff';
    ctx.fillText('INDRIYO', 16, 25);
    ctx.fillStyle = '#ff9d00';
    ctx.font = 'bold 10px sans-serif';
    ctx.fillText('ইন্দ্রিয় ADAS', 78, 24);

    // Motorcycle Speed
    ctx.font = '900 18px monospace';
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'center';
    ctx.fillText(`${this.bikeSpeedKmh.toFixed(0)} KM/H`, w * 0.5, 26);

    // Threat status
    ctx.textAlign = 'right';
    ctx.font = 'bold 11px monospace';
    if (highestThreat === 3) {
      ctx.fillStyle = '#ff2a4b';
      ctx.fillText('● CRITICAL THREAT', w - 16, 25);
    } else if (highestThreat === 2) {
      ctx.fillStyle = '#ff9d00';
      ctx.fillText('● BLIND SPOT ALERT', w - 16, 25);
    } else {
      ctx.fillStyle = '#30d158';
      ctx.fillText('● ALL CLEAR', w - 16, 25);
    }
    ctx.restore();
  }
}

// Attach to window
window.AdasSimulator = AdasSimulator;
