handleTextInput(tb, event) {
  // Попробуем простой вариант: обновляем текст напрямую
  tb.text = event.target.innerHTML; // Используем innerHTML
  // Сохранение может происходить здесь, или при потере фокуса/Enter
  // this.saveTextBlocksToDrawingData(); // Пока закомментируем прямое сохранение при каждом вводе
},

handleTextBlur(tb) {
  // Обновляем и сохраняем текст при потере фокуса
  const blockEl = event.target; // Получаем элемент из события blur
  if (blockEl) {
    tb.text = blockEl.innerHTML; // Используем innerHTML для сохранения форматирования
    this.saveTextBlocksToDrawingData(); // Сохраняем здесь
  }
  // ... existing code ...
},

handleCanvasClick(event) {
  if (this.currentDrawingTool === 'text') {
    const rect = this.$refs.drawingCanvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / this.scale - this.translateX / this.scale;
    const y = (event.clientY - rect.top) / this.scale - this.translateY / this.scale;
    const newBlock = {
      id: Date.now() + Math.random(),
      x,
      y,
      width: 180,
      height: 40,
      text: ' ', // Начинаем с пробела, чтобы блок был виден
      styles: {
        fontFamily: 'Rubik, Segoe UI, Arial, sans-serif',
        fontSize: 18,
        fontWeight: 400,
        color: '#222',
        textAlign: 'left',
      },
      selected: true,
      editing: true,
    };
    this.textBlocks.push(newBlock);
    this.deselectAllTextBlocksExcept(newBlock.id);
    this.saveTextBlocksToDrawingData();
    this.$nextTick(() => {
      const blockEl = this.$el.querySelector(`[contenteditable][tabindex][data-id='${newBlock.id}']`);
      if (blockEl) {
        blockEl.focus();
        // Устанавливаем курсор в конец текста
        const range = document.createRange();
        const sel = window.getSelection();
        range.selectNodeContents(blockEl);
        range.collapse(false);
        sel.removeAllRanges();
        sel.addRange(range);
      }
    });
  }
},

<template>
<div v-for="tb in textBlocks" :key="tb.id"
  :data-id="tb.id"
  :style="{
    position: 'absolute',
    left: tb.x + 'px',
    top: tb.y + 'px',
    width: tb.width + 'px',
    minHeight: tb.height + 'px',
    zIndex: 20,
    cursor: tb.editing ? 'text' : (draggingBlockId === tb.id ? 'grabbing' : 'move'),
  }"
  @mousedown.stop="handleTextBlockClick(tb, $event)"
  tabindex="0"
  @contextmenu.stop.prevent="handleTextBlockContextMenu(tb, $event)"
>
  <div
    :style="{
      background: tb.selected || tb.editing ? 'rgba(255,255,255,0.95)' : 'transparent',
      border: tb.selected || tb.editing ? '2px solid #0d6efd' : 'none',
      borderRadius: tb.selected || tb.editing ? '8px' : '0',
      boxShadow: tb.selected || tb.editing ? '0 2px 12px rgba(13,110,253,0.10)' : 'none',
      padding: tb.selected || tb.editing ? '8px 12px' : '0',
      fontFamily: tb.styles.fontFamily,
      fontSize: tb.styles.fontSize + 'px',
      fontWeight: tb.styles.fontWeight,
      color: tb.styles.color,
      textAlign: tb.styles.textAlign,
      outline: 'none',
      userSelect: tb.editing ? 'text' : 'none',
      fontStyle: tb.styles.fontStyle,
      textDecoration: tb.styles.textDecoration,
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      width: '100%',
      minHeight: '100%',
    }"
    :contenteditable="tb.editing"
    @input="handleTextInput(tb, $event)"
    @blur="handleTextBlur(tb)"
    @keydown="handleTextKeydown(tb, $event)"
    v-html="tb.text"
  >
  </div>

  <!-- Маркеры resize только у активного блока -->
  <template v-if="tb.selected || tb.editing">
    <div v-for="corner in ['tl','tr','bl','br']" :key="corner"
      class="resize-marker"
      :class="'resize-' + corner"
      @mousedown.stop="startResize(tb, $event, corner)"
    ></div>
  </template>
</div> 
</template>

<script>
// ... existing code ...
</script> 