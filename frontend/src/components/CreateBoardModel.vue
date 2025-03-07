<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <h3>Создать новую доску</h3>
      <input
        ref="input"
        v-model="boardName"
        placeholder="Введите название доски"
        class="board-name-input"
        @keyup.enter="create"
      />
      <div class="modal-actions">
        <button @click="create" class="confirm-btn">Создать</button>
        <button @click="close" class="cancel-btn">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      boardName: 'Новая доска'
    }
  },
  mounted() {
    this.$refs.input.focus()
    document.body.style.overflow = 'hidden'
  },
  beforeDestroy() {
    document.body.style.overflow = 'auto'
  },
  methods: {
    create() {
      if (this.boardName.trim()) {
        this.$emit('create', this.boardName.trim())
      }
      this.close()
    },
    close() {
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.board-name-input {
  width: 100%;
  padding: 12px;
  margin: 16px -16px;
  border: 2px solid #0079bf;
  border-radius: 4px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.confirm-btn {
  background: #0079bf;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.confirm-btn:hover {
  background: #026aa7;
}

.cancel-btn {
  background: #f0f0f0;
  color: #5e6c84;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.cancel-btn:hover {
  background: #e0e0e0;
}
</style>