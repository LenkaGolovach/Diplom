<template>
  <div class="timer-end-modal-overlay" @click.self="close">
    <div class="timer-end-modal-content">
      <h3 class="timer-end-modal-title">
        <i class="fas fa-clock"></i> Таймер завершен
      </h3>
      <p class="timer-end-modal-message">
        Таймер "{{ timerName }}" завершил свою работу
      </p>
      <div class="timer-end-modal-actions">
        <button @click="close" class="close-btn">
          <i class="fas fa-check"></i> Понятно
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    timerName: {
      type: String,
      default: 'Задача'
    }
  },
  methods: {
    close() {
      this.$emit('close');
    }
  },
  mounted() {
    document.body.style.overflow = 'hidden';
  },
  beforeDestroy() {
    document.body.style.overflow = 'auto';
  }
}
</script>

<style scoped>
.timer-end-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
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

.timer-end-modal-content {
  background: rgba(255, 255, 255, 0.9);
  padding: 30px;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  z-index: 2001;
  animation: slideIn 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.timer-end-modal-title {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 20px;
  text-align: center;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #2c3e50;
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.timer-end-modal-title i {
  color: #5b9cff;
}

.timer-end-modal-message {
  font-size: 16px;
  line-height: 1.5;
  color: #4a5568;
  text-align: center;
  margin-bottom: 20px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.2px;
}

.timer-end-modal-actions {
  margin-top: 25px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.close-btn {
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}
</style> 