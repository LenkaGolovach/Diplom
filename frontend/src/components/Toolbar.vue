<template>
  <div class="toolbar">
    <button 
      :class="{ active: currentTool === 'cursor' }" 
      @click="selectTool('cursor')" 
      title="Курсор (V)">
      🖐️
    </button>
    <button 
      :class="{ active: currentTool === 'pencil' }" 
      @click="selectTool('pencil')" 
      title="Карандаш (P)">
      ✏️
    </button>
    <button 
      :class="{ active: currentTool === 'line' }" 
      @click="selectTool('line')" 
      title="Линия (L)">
      ➖
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
  padding: 6px;
  border-radius: 8px; /* Скругленные углы для всего тулбара */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  display: flex;
  gap: 4px; /* Небольшой отступ между кнопками */
  z-index: 200; /* Выше большинства элементов */
}

.toolbar button {
  background-color: transparent; /* Без фона по умолчанию */
  border: none; /* Убираем стандартную границу */
  color: #e0e0e0; /* Светлый цвет для иконок/текста */
  padding: 8px 10px;
  border-radius: 6px; /* Скругленные углы для кнопок */
  cursor: pointer;
  font-size: 18px; /* Размер эмодзи/иконок */
  line-height: 1; /* Для лучшего вертикального выравнивания эмодзи */
  transition: background-color 0.2s ease, color 0.2s ease;
}

.toolbar button:hover {
  background-color: #444444; /* Легкое выделение при наведении */
  color: #ffffff;
}

.toolbar button.active {
  background-color: #0d6efd; /* Синий фон для активной кнопки */
  color: white;
}
</style> 