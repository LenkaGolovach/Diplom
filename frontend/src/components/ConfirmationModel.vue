<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <h3>{{ title }}</h3>
      <p>{{ message }}</p>
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
  z-index: 1001;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  z-index: 1002;
}

.modal-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.confirm-btn {
  background: #ff4444;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-btn {
  background: #f0f0f0;
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}
</style>