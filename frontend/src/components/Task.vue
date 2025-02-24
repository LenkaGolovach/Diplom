<template>
  <div class="task" @click="$emit('click', task)">
    <div class="task-header">
      <span>{{ task.name }}</span>
      <button @click.stop="$emit('delete')">×</button>
    </div>
    <!-- Прогресс-бар (только если есть подзадачи) -->
    <div v-if="task.subtasks && task.subtasks.length > 0" class="progress-bar">
      <div class="progress" :style="{ width: progress + '%' }"></div>
    </div>
    <div v-if="task.subtasks && task.subtasks.length > 0" class="progress-text">
      {{ progress }}% выполнено
    </div>
    <div class="file-previews">
        <div 
          v-for="(file, index) in visibleFiles" 
          :key="index" 
          class="file-preview-badge"
          :class="{ 'image-preview': isImage(file.type) }"
          @click="downloadFile(file)"
        >
          <img v-if="!isImage(file.type)" src="/icons/file-icon.png" alt="Document Icon" class="file-icon-img">
          <img v-else :src="file.url" alt="Preview">
        </div>
        <div v-if="hiddenFilesCount > 0" class="more-files">
          +{{ hiddenFilesCount }}
        </div>
      </div>
  </div>
</template>

<script>
export default {
  props: {
    task: Object,
  },
  computed: {
    progress() {
      if (!this.task.subtasks || this.task.subtasks.length === 0) return 0;
      const completed = this.task.subtasks.filter(s => s.completed).length;
      return Math.round((completed / this.task.subtasks.length) * 100);
    },
    visibleFiles() {
      return (this.task.files && this.task.files.slice(0, 3)) || [];
    },
    hiddenFilesCount() {
      return Math.max((this.task.files && this.task.files.length || 0) - 3, 0);
    },
    isImage() {
      return type => type && type.startsWith('image/');
    },
  },
  methods: {
    downloadFile(file) {
      // Создаем временную ссылку для скачивания
      const link = document.createElement('a');
      link.href = file.url;
      link.download = file.name; // Имя файла при скачивании
      document.body.appendChild(link);
      link.click(); // Инициируем скачивание
      document.body.removeChild(link); // Удаляем ссылку после скачивания
    }
  }
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

.file-previews {
  display: flex;
  gap: 5px;
  margin-left: auto;
  padding-right: 10px;
}

.file-preview-badge {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8em;
  position: relative;
  cursor: pointer;
}

.file-preview-badge img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.more-files {
  background: #e0e0e0;
  padding: 0 5px;
  border-radius: 4px;
  font-size: 0.8em;
}

.file-icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Сохраняет пропорции */
}
</style>
