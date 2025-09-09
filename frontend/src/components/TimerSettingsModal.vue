<template>
  <div class="timer-settings-modal-overlay" @click.self="cancel">
    <div class="timer-settings-modal-content">
      <h3 class="timer-settings-modal-title">Настройка таймера</h3>
      
      <div class="timer-settings-form">
        <input
          v-model="localTimerName"
          class="timer-name-input"
          placeholder="Название таймера"
        />
        
        <div class="timer-controls">
          <div class="timer-input-group">
            <label>Часы</label>
            <input
              v-model.number="localTimerHours"
              type="number"
              min="0"
              max="23"
              class="timer-input"
            />
          </div>
          <div class="timer-input-group">
            <label>Минуты</label>
            <input
              v-model.number="localTimerMinutes"
              type="number"
              min="0"
              max="59"
              class="timer-input"
            />
          </div>
          <div class="timer-input-group">
            <label>Секунды</label>
            <input
              v-model.number="localTimerSeconds"
              type="number"
              min="0"
              max="59"
              class="timer-input"
            />
          </div>
        </div>
      </div>
      
      <div class="timer-settings-actions">
        <button @click="startTimer" class="start-timer-btn">Создать</button>
        <button @click="cancel" class="cancel-btn">Отмена</button>
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
    },
    timerHours: {
      type: Number,
      default: 0
    },
    timerMinutes: {
      type: Number,
      default: 5
    },
    timerSeconds: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      localTimerName: this.timerName,
      localTimerHours: this.timerHours,
      localTimerMinutes: this.timerMinutes,
      localTimerSeconds: this.timerSeconds
    };
  },
  methods: {
    startTimer() {
      // Проверка на корректность введенных значений
      this.localTimerHours = Math.max(0, Math.min(23, this.localTimerHours || 0));
      this.localTimerMinutes = Math.max(0, Math.min(59, this.localTimerMinutes || 0));
      this.localTimerSeconds = Math.max(0, Math.min(59, this.localTimerSeconds || 0));
      
      // Проверяем, что хотя бы одно значение больше нуля
      if (this.localTimerHours === 0 && this.localTimerMinutes === 0 && this.localTimerSeconds === 0) {
        // По умолчанию устанавливаем 5 минут
        this.localTimerMinutes = 5;
      }
      
      // Если название не задано, устанавливаем значение по умолчанию
      if (!this.localTimerName.trim()) {
        this.localTimerName = 'Задача';
      }
      
      this.$emit('start', {
        name: this.localTimerName,
        hours: this.localTimerHours,
        minutes: this.localTimerMinutes,
        seconds: this.localTimerSeconds
      });
    },
    cancel() {
      this.$emit('cancel');
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
.timer-settings-modal-overlay {
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
}

.timer-settings-modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  width: 450px;
  max-width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.timer-settings-modal-title {
  font-size: 1.8em;
  font-weight: 600;
  margin-bottom: 25px;
  text-align: center;
  color: #2c3e50;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.timer-settings-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.timer-name-input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.2px;
}

.timer-name-input:focus {
  border-color: #5b9cff;
  box-shadow: 0 0 0 3px rgba(91, 156, 255, 0.2);
}

.timer-controls {
  display: flex;
  gap: 15px;
  justify-content: space-between;
}

.timer-input-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex: 1;
}

.timer-input-group label {
  font-size: 14px;
  color: #4a5568;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.timer-input {
  width: 100%;
  padding: 12px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.timer-input:focus {
  border-color: #5b9cff;
  box-shadow: 0 0 0 3px rgba(91, 156, 255, 0.2);
}

.timer-settings-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.start-timer-btn {
  background: #5b9cff;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.start-timer-btn:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
}

.cancel-btn {
  background: transparent;
  color: #4a5568;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Poppins', 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.cancel-btn:hover {
  background: #f5f5f5;
}
</style> 