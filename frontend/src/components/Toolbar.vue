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
      @click="selectTool('pencil')" 
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
      :class="{ active: currentTool === 'eraser' }" 
      @click="selectTool('eraser')" 
      title="Ластик (E)">
      <i class="fas fa-eraser"></i>
    </button>
    <!-- Другие инструменты будут добавлены сюда -->
  </div>
</template>

<script>
export default {
  name: 'Toolbar',
  props: {
    currentTool: {
      type: String,
      default: 'cursor',
    }
  },
  methods: {
    selectTool(toolName) {
      this.$emit('tool-selected', toolName);
    }
  }
};
</script>

<style scoped>
.toolbar {
  position: fixed; /* Позиционируем относительно viewport */
  bottom: 20px; /* Отступ снизу */
  left: 50%;
  transform: translateX(-50%); /* Центрируем по горизонтали */
  background-color: #2c2c2c; /* Темный фон как в Figma */
  padding: 8px;
  border-radius: 10px; /* Скругленные углы для всего тулбара */
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  display: flex;
  gap: 6px; /* Небольшой отступ между кнопками */
  z-index: 200; /* Выше большинства элементов */
}

.toolbar button {
  background-color: rgba(255, 255, 255, 0.05); /* Слегка заметный фон для кнопок */
  border: none; /* Убираем стандартную границу */
  color: #e0e0e0; /* Светлый цвет для иконок/текста */
  padding: 10px 12px;
  border-radius: 8px; /* Скругленные углы для кнопок */
  cursor: pointer;
  font-size: 16px; /* Размер иконок */
  line-height: 1; /* Для лучшего вертикального выравнивания */
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
  background-color: #0d6efd; /* Синий фон для активной кнопки */
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 3px 12px rgba(13, 110, 253, 0.4);
}

.toolbar button i {
  font-size: 18px;
}
</style> 