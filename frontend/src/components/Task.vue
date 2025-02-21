<template>
  <div class="task" @click="$emit('click', task)">
    <div class="task-header">
      <span>{{ task.name }}</span>
      <button @click.stop="$emit('delete')">Удалить</button>
    </div>
    <!-- Прогресс-бар -->
    <div class="progress-bar">
      <div class="progress" :style="{ width: progress + '%' }"></div>
    </div>
    <div class="progress-text">{{ progress }}% выполнено</div>
  </div>
</template>

<script>
export default {
  props: {
    task: Object,
  },
  computed: {
    // Вычисляем прогресс выполнения подзадач
    progress() {
      const totalSubtasks = this.task.subtasks.length;
      if (totalSubtasks === 0) return 0;
      const completedSubtasks = this.task.subtasks.filter(
        (subtask) => subtask.completed
      ).length;
      return Math.round((completedSubtasks / totalSubtasks) * 100);
    },
  },
  methods: {
    deleteTask() {
      this.$emit('delete');
    },
  },
};
</script>

<style scoped>
.task {
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 3px;
  background-color: #f9f9f9;
  cursor: pointer;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.task-header button {
  background: #ff6b6b;
  border: none;
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.task-header button:hover {
  background: #ff4c4c;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 5px;
}

.progress {
  height: 100%;
  background: #76c7c0;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8em;
  color: #555;
  text-align: right;
}
</style>
