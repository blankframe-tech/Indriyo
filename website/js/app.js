/**
 * Indriyo Showcase Application UI Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Simulator
  const sim = new window.AdasSimulator('adasCanvas', 'simDisplayFrame');

  // 2. Scenario Switchers
  const scenarioBtns = document.querySelectorAll('.sim-scenario-btn');
  scenarioBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      scenarioBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const scenario = btn.getAttribute('data-scenario');
      sim.initScenario(scenario);
    });
  });

  // 3. Bike Speed Slider
  const speedSlider = document.getElementById('speedSlider');
  const speedValueDisplay = document.getElementById('speedValueDisplay');
  if (speedSlider && speedValueDisplay) {
    speedSlider.addEventListener('input', (e) => {
      const speed = parseFloat(e.target.value);
      speedValueDisplay.textContent = `${speed} KM/H`;
      sim.setSpeed(speed);
    });
  }

  // 4. Sound Toggle
  const soundBtn = document.getElementById('toggleSoundBtn');
  if (soundBtn) {
    soundBtn.addEventListener('click', () => {
      const enabled = sim.toggleSound();
      soundBtn.classList.toggle('active', enabled);
      soundBtn.innerHTML = enabled ? '🔊 Audio Alerts: ON' : '🔇 Audio Alerts: OFF';
    });
  }

  // 5. Grid Toggle
  const gridBtn = document.getElementById('toggleGridBtn');
  if (gridBtn) {
    gridBtn.addEventListener('click', () => {
      const active = sim.toggleGrid();
      gridBtn.classList.toggle('active', active);
    });
  }

  // 6. Box Toggle
  const boxesBtn = document.getElementById('toggleBoxesBtn');
  if (boxesBtn) {
    boxesBtn.addEventListener('click', () => {
      const active = sim.toggleBoxes();
      boxesBtn.classList.toggle('active', active);
    });
  }

  // 7. BOM Calculator Strategy Tabs
  const bomData = {
    strat2: {
      title: "Strategy 2: The Smartphone Brain (Under ৳3,000)",
      total: "৳2,850 BDT",
      items: [
        { name: "2x ESP32-CAM + OV2640 Modules", note: "Video capture & SoftAP MJPEG stream", price: "৳1,800" },
        { name: "1x ESP32-CAM-MB USB Programmer", note: "One-time code flashing base", price: "৳350" },
        { name: "1x LM2596 Step-Down Buck Converter (3A)", note: "Drops 12V bike battery to 5.1V", price: "৳220" },
        { name: "2x 1000µF 16V Electrolytic Capacitors", note: "Brownout protection buffer", price: "৳20" },
        { name: "1x Inline 3A Waterproof Fuse Holder", note: "Battery short-circuit safety", price: "৳120" },
        { name: "Custom 3D Printed Tail Mount Pod", note: "Nilkhet/Daraz 3D print service", price: "৳340" }
      ]
    },
    strat1: {
      title: "Strategy 1: Low-Cost Linux NPU Board (Under ৳14,000)",
      total: "৳13,400 BDT",
      items: [
        { name: "1x Luckfox Pico Pro (RV1106 0.5 TOPS NPU)", note: "Edge AI object detection & Linux OS", price: "৳3,800" },
        { name: "1x SC3336 3MP Ultra-Wide Camera", note: "MIPI CSI 170° high dynamic range", price: "৳2,200" },
        { name: "1x 4.3-inch IPS LCD Display (800x480)", note: "Daylight readable digital mirror", price: "৳4,500" },
        { name: "1x 12V to 5V 5A Step-Down Module", note: "High amperage clean power", price: "৳600" },
        { name: "1x ELM327 Bluetooth OBD-II Scanner", note: "Direct bike road speed ingestion", price: "৳800" },
        { name: "Weatherproof Enclosure & RAM Mount", note: "Handlebar clamp & 3D body", price: "৳1,500" }
      ]
    },
    strat3: {
      title: "Strategy 3: The 24GHz Millimeter-Wave Radar Hybrid",
      total: "৳3,850 BDT",
      items: [
        { name: "1x ESP32 NodeMCU Development Board", note: "Dual-core processor & Bluetooth", price: "৳580" },
        { name: "2x HLK-LD1125H 24GHz mmWave Radars", note: "Left and Right blind spot distance/speed", price: "৳2,400" },
        { name: "2x WS2812B NeoPixel RGB LED Strips", note: "Windshield/mirror perimeter warning lights", price: "৳350" },
        { name: "1x LM2596 Step-Down Buck Converter", note: "12V to 5V power supply", price: "৳220" },
        { name: "1x Inline Fuse & Wiring Harness", note: "Motorcycle waterproof harness", price: "৳300" }
      ]
    }
  };

  const bomTabBtns = document.querySelectorAll('.bom-tab-btn');
  const bomListEl = document.getElementById('bomList');
  const bomTotalEl = document.getElementById('bomTotal');

  function renderBom(stratKey) {
    const data = bomData[stratKey];
    if (!data || !bomListEl || !bomTotalEl) return;

    bomTotalEl.textContent = data.total;
    bomListEl.innerHTML = data.items.map(item => `
      <div class="bom-item">
        <div>
          <div class="bom-item-name">${item.name}</div>
          <div class="bom-item-note">${item.note}</div>
        </div>
        <div class="bom-item-price">${item.price}</div>
      </div>
    `).join('');
  }

  bomTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      bomTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const strat = btn.getAttribute('data-strat');
      renderBom(strat);
    });
  });

  // Render default BOM
  renderBom('strat2');
});
