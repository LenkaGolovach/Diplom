<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <h3 class="modal-title">Создать новую доску</h3>
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
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-content {
  background: rgba(255, 255, 255, 0.9);
  padding: 30px;
  border-radius: 12px;
  width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  z-index: 1002;
  animation: slideIn 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.modal-title {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 20px;
  text-align: center;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #2c3e50;
  letter-spacing: 0.3px;
}

.board-name-input {
  width: 100%;
  padding: 15px;
  margin: 20px -15px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 16px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.board-name-input:focus {
  border-color: #5a9bd4;
  box-shadow: 0 0 0 3px rgba(90, 155, 212, 0.2);
  outline: none;
}

.modal-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 25px;
}

.confirm-btn {
  background: #5b9cff;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
  letter-spacing: 0.3px;
}

.confirm-btn:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.cancel-btn {
  background: #f0f0f0;
  color: #5e6c84;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 0.3px;
}

.cancel-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}
</style>