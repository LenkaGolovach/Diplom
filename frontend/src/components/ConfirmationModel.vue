<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <h3 class="modal-title">{{ title }}</h3>
      <p class="modal-message">{{ message }}</p>
      <div class="modal-actions">
        <button @click="confirm" class="confirm-btn">{{ confirmText }}</button>
        <button @click="close" class="cancel-btn">{{ cancelText }}</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    title: {
      type: String,
      default: 'Подтверждение действия'
    },
    message: {
      type: String,
      default: 'Вы уверены, что хотите выполнить это действие?'
    },
    confirmText: {
      type: String,
      default: 'Подтвердить'
    },
    cancelText: {
      type: String,
      default: 'Отмена'
    }
  },
  methods: {
    confirm() {
      this.$emit('confirm');
      this.close();
    },
    close() {
      this.$emit('close');
    }
  },
  mounted() {
    document.body.style.overflow = 'hidden'
  },
  beforeDestroy() {
    document.body.style.overflow = 'auto'
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
  max-width: 90%;
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

.modal-message {
  font-size: 16px;
  line-height: 1.5;
  color: #4a5568;
  text-align: center;
  margin-bottom: 20px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.2px;
}

.modal-actions {
  margin-top: 25px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.confirm-btn {
  background: #ff7b93;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(255, 123, 147, 0.3);
  letter-spacing: 0.3px;
}

.confirm-btn:hover {
  background: #ff6a85;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 123, 147, 0.4);
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