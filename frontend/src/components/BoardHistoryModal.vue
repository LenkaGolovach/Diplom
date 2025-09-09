<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="close-btn" @click="$emit('close')">×</button>
      <h2 class="modal-title">История проекта</h2>
      <div v-if="events.length === 0" class="no-history">Нет истории действий</div>
      <ul v-else class="history-list">
        <li v-for="(e, idx) in events" :key="idx" class="history-item">
          <div class="history-marker"></div>
          <div class="history-content">
            <div class="history-header">
              <span class="history-user">{{ e.user_name }}</span>
              <span class="history-ts">{{ formatTs(e.ts) }}</span>
            </div>
            <div class="history-action">{{ e.text }}</div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
export default {
  props: {
    boardId: { type: [String,Number], required: true },
    currentUser: { type: Object, required: true }
  },
  data() {
    return { events: [] };
  },
  async created() {
    // получаем историю с бэка
    try {
      const res = await axios.get(`/api/boards/${this.boardId}/history/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      // приводим каждую запись к нужному тексту
      this.events = res.data.map(evt => ({
            user_name: evt.user,
            text: evt.action, // Используем готовый текст из бэкенда
            ts: evt.ts
        }));
    } catch (e) {
      console.error('Не смогли загрузить историю:', e);
    }
  },
  methods: {
    formatTs(ts) {
      const d = new Date(ts);
      return d.toLocaleString('ru-RU', { day:'2-digit',month:'2-digit',year:'numeric', hour:'2-digit', minute:'2-digit' });
    }
  }
};
</script>

<style scoped>
.history-list {
  position: relative;
  margin: 0;
  padding: 20px 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.history-list::before {
  content: '';
  position: absolute;
  left: 20px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e2e8f0;
}

.history-item {
  position: relative;
  display: flex;
  margin-bottom: 24px;
  padding-left: 40px;
}

.history-marker {
  position: absolute;
  left: 12px;
  top: 4px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #5b9cff;
  box-shadow: 0 0 0 4px rgba(91,156,255,0.2);
}

.history-content {
  background: rgba(255,255,255,0.8);
  border-radius: 8px;
  padding: 14px 18px; /* чуть больше отступы для визуального баланса */
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  flex: 1;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.history-user {
  font-weight: 600;
  color: #2c3e50;
  font-size: 16px; /* увеличили с 14px */
}

.history-ts {
  font-size: 13px; /* увеличили с 12px */
  color: #94a3b8;
}

.history-action {
  font-size: 16px; /* увеличили с 14px */
  color: #4a5568;
  line-height: 1.5;
}

.no-history {
  padding: 40px;
  text-align: center;
  color: #64748b;
  font-style: italic;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  font-size: 16px; /* чуть увеличили размер */
}

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

.modal-content {
  background: rgba(255, 255, 255, 0.9);
  padding: 35px 30px;
  border-radius: 12px;
  max-width: 550px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  z-index: 1002;
  animation: slideIn 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.4);
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.modal-content::-webkit-scrollbar {
  width: 5px;
}

.modal-content::-webkit-scrollbar-track {
  background: transparent;
}

.modal-content::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
}

.modal-title {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 25px;
  text-align: center;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #2c3e50;
  letter-spacing: 0.3px;
}

.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 8px 15px;
  border-radius: 8px;
  color: #4a5568;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}
</style>
