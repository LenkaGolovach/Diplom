<template>
  <div class="toolbar">
    <button 
      :class="{ active: currentTool === 'cursor' }" 
      @click="selectTool('cursor')" 
      title="Курсор (V)">
      <i class="fas fa-mouse-pointer"></i>
    </button>
    <button 
      :class="{ active: currentTool === 'pencil' }" 
      @click="togglePencilPanel" 
      title="Карандаш (P)">
      <i class="fas fa-pencil-alt"></i>
    </button>
    <button 
      :class="{ active: currentTool === 'line' }" 
      @click="selectTool('line')" 
      title="Линия (L)">
      <i class="fas fa-slash"></i>
    </button>
    <button 
      :class="{ active: currentTool === 'text' }" 
      @click="selectTool('text')" 
      title="Текст (T)">
      <i class="fas fa-t"></i>
    </button>
    <!-- Кнопка ластика убрана -->

    <!-- Горизонтальная панель параметров карандаша/ластика -->
    <div v-if="showPencilPanel" class="tool-popup tool-popup-horizontal">
      <!-- Цвета (неактивны если ластик) -->
      <div class="popup-section colors" v-if="!eraserMode">
        <div class="popup-label">Цвет</div>
        <div class="color-palette-horizontal">
          <div
            v-for="color in colors"
            :key="color"
            :style="{ background: color }"
            :class="['color-dot', { selected: currentColor === color }]"
            @click="selectColor(color)"
          ></div>
        </div>
      </div>
      <!-- Толщина линии (неактивна если ластик) -->
      <div class="popup-section thickness" v-if="!eraserMode">
        <div class="popup-label">Толщина</div>
        <input
          type="range"
          min="1"
          max="20"
          v-model.number="localLineWidth"
          @input="selectLineWidth(localLineWidth)"
        />
        <div class="slider-value">{{ localLineWidth }} px</div>
      </div>
      <!-- Переключатель карандаша (только если активен ластик) -->
      <div class="popup-section pencil-toggle" v-if="eraserMode">
        <div class="popup-label">Карандаш</div>
        <button class="pencil-btn" :class="{ active: !eraserMode }" @click="toggleEraserMode" title="Карандаш">
          <i class="fas fa-pencil-alt"></i>
        </button>
      </div>
      <!-- Переключатель ластика -->
      <div class="popup-section eraser-toggle">
        <div class="popup-label">Ластик</div>
        <button class="eraser-btn" :class="{ active: eraserMode }" @click="toggleEraserMode" title="Ластик">
          <i class="fas fa-eraser"></i>
        </button>
      </div>
      <!-- Размер ластика -->
      <div class="popup-section eraser-size" v-if="eraserMode">
        <div class="popup-label">Размер</div>
        <input
          type="range"
          min="5"
          max="60"
          v-model.number="localEraserSize"
          @input="selectEraserSize(localEraserSize)"
        />
        <div class="slider-value">{{ localEraserSize }} px</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Toolbar',
  props: {
    currentTool: {
      type: String,
      default: 'cursor',
    },
    currentColor: {
      type: String,
      default: '#222',
    },
    currentLineWidth: {
      type: Number,
      default: 4,
    },
    currentEraserSize: {
      type: Number,
      default: 20,
    },
    eraserMode: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showPencilPanel: false,
      colors: [
        '#222', '#eb5a46', '#f2d600', '#61bd4f', '#0079bf', '#c377e0', '#b87333', '#fff'
      ],
      localLineWidth: this.currentLineWidth,
      localEraserSize: this.currentEraserSize,
    };
  },
  watch: {
    currentLineWidth(val) { this.localLineWidth = val; },
    currentEraserSize(val) { this.localEraserSize = val; },
    currentTool(val) {
      if (val !== 'pencil') this.showPencilPanel = false;
    }
  },
  methods: {
    selectTool(toolName) {
      this.$emit('tool-selected', toolName);
    },
    togglePencilPanel() {
      if (this.showPencilPanel) {
        this.showPencilPanel = false;
        this.selectTool('cursor');
      } else {
        this.showPencilPanel = true;
        this.selectTool('pencil');
      }
    },
    selectColor(color) {
      if (!this.eraserMode) this.$emit('color-selected', color);
    },
    selectLineWidth(width) {
      if (!this.eraserMode) this.$emit('line-width-selected', width);
    },
    selectEraserSize(size) {
      if (this.eraserMode) this.$emit('eraser-size-selected', size);
    },
    toggleEraserMode() {
      this.$emit('eraser-mode-toggled', !this.eraserMode);
    },
  },
};
</script>

<style scoped>
.toolbar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #2c2c2c;
  padding: 8px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  display: flex;
  gap: 6px;
  z-index: 200;
}
.toolbar button {
  background-color: rgba(255, 255, 255, 0.05);
  border: none;
  color: #e0e0e0;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
}
.toolbar button:hover {
  background-color: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}
.toolbar button.active {
  background-color: #0d6efd;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 3px 12px rgba(13, 110, 253, 0.4);
}
.toolbar button i {
  font-size: 18px;
}
.tool-popup-horizontal {
  position: absolute;
  left: 50%;
  bottom: 100%;
  transform: translateX(-50%);
  margin-bottom: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.13);
  padding: 14px 18px 10px 18px;
  min-width: 90px;
  display: flex;
  flex-direction: row;
  align-items: center;
  z-index: 300;
  animation: fadeIn 0.18s;
  gap: 24px;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.popup-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 0;
  min-width: 70px;
}
.popup-label {
  font-size: 13px;
  color: #888;
  margin-bottom: 6px;
  font-weight: 500;
}
.color-palette-horizontal {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
}
.color-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #eee;
  cursor: pointer;
  transition: border 0.15s, box-shadow 0.15s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.color-dot.selected {
  border: 3px solid #0d6efd;
  box-shadow: 0 2px 8px rgba(13,110,253,0.13);
}
.slider-value {
  font-size: 13px;
  color: #444;
  margin-top: 2px;
  text-align: center;
}
input[type="range"] {
  width: 70px;
  margin: 0 auto;
  accent-color: #0d6efd;
}
.eraser-btn {
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.eraser-btn.active, .eraser-btn:hover {
  background: #0d6efd;
  color: #fff;
}
.pencil-btn {
  background: #f5f5f5;
  border: none;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.pencil-btn.active, .pencil-btn:hover {
  background: #0d6efd;
  color: #fff;
}
.text-svg-icon {
  display: block;
  filter: drop-shadow(0 1px 4px rgba(0,0,0,0.13));
}
button.active .text-svg-icon text {
  fill: #fff;
}
button:not(.active) .text-svg-icon text {
  fill: #e0e0e0;
}
</style> 