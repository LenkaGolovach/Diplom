<template>
  <div class="task" @click="$emit('click', task)">
    <div class="task-header">
      <span>{{ task.name }}</span>
      <button @click.stop="$emit('delete', task)">×</button>
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
        v-for="(attachment, index) in visibleAttachments" 
        :key="index" 
        class="file-preview-badge"
        :class="{ 'image-preview': isImage(attachment.file) }"
        @click.stop="downloadFile(attachment)"
      >
        <img v-if="!isImage(attachment.file)" src="/icons/file-icon.png" alt="Document Icon" class="file-icon-img">
        <img v-else :src="attachment.url" alt="Preview">
      </div>
      <div v-if="hiddenAttachmentsCount > 0" class="more-files">
        +{{ hiddenAttachmentsCount }}
      </div>
    </div>
    <div class="task-footer">
      <div class="participants-preview">
        <div 
          v-for="member in task.members.slice(0, 3)" 
          :key="member.email"
          class="participant-avatar"
        >
          <img 
            :src="member.avatar || '/default-avatar.png'" 
            class="avatar"
            :title="member.email"
          >
        </div>
        <div 
          v-if="task.members.length > 3" 
          class="more-participants"
        >
          +{{ task.members.length - 3 }}
        </div>
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
    visibleAttachments() {
      return (this.task.attachments && this.task.attachments.slice(0, 3)) || [];
    },
    hiddenAttachmentsCount() {
      return Math.max((this.task.attachments && this.task.attachments.length || 0) - 3, 0);
    },
    isImage() {
      return filePath => filePath && (
        filePath.endsWith('.jpg') || 
        filePath.endsWith('.jpeg') || 
        filePath.endsWith('.png') || 
        filePath.endsWith('.gif') || 
        filePath.endsWith('.svg')
      );
    },
  },
  methods: {
    downloadFile(attachment) {
      // Предотвращаем всплытие события клика
      event.stopPropagation();
      
      // Создаем временную ссылку для скачивания
      const link = document.createElement('a');
      link.href = attachment.url || attachment.file;
      link.download = attachment.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }
};
</script>

<style scoped>
.task {
  padding: 15px;
  margin: 10px 5px;
  border: none;
  border-radius: 8px;
  background-color: white;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

.task:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  position: relative;
}

.task-header span {
  font-weight: 600;
  font-size: 15px;
  color: #2c3e50;
  line-height: 1.4;
  word-break: break-word;
  flex: 1;
  padding-right: 10px;
  letter-spacing: 0.2px;
}

.task-header button {
  background: transparent;
  border: none;
  color: #bdc3c7;
  font-size: 18px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
  margin-top: -5px;
  margin-right: -5px;
}

.task-header button:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  transform: rotate(90deg);
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: #ecf0f1;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress {
  height: 100%;
  background: linear-gradient(to right, #5b9cff, #82c0ff);
  transition: width 0.4s ease;
}

.progress-text {
  font-size: 0.75em;
  color: #7f8c8d;
  text-align: right;
  margin-bottom: 12px;
  letter-spacing: 0.2px;
}

.file-previews {
  display: flex;
  gap: 6px;
  margin: 5px 0;
  flex-wrap: wrap;
}

.file-preview-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8em;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #ecf0f1;
  overflow: hidden;
}

.file-preview-badge:hover {
  transform: scale(1.1);
}

.file-preview-badge img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.more-files {
  background: #e0e0e0;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 0.8em;
  height: 28px;
  display: flex;
  align-items: center;
  color: #7f8c8d;
}

.file-icon-img {
  width: 80%;
  height: 80%;
  object-fit: contain;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f5f5f5;
}

.participants-preview {
  display: flex;
  gap: 5px;
}

.participant-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.participant-avatar:hover {
  transform: scale(1.15);
  z-index: 2;
}

.participant-avatar:not(:first-child) {
  margin-left: -12px;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.more-participants {
  background: #f0f0f0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75em;
  color: #7f8c8d;
  margin-left: -12px;
  border: 2px solid white;
  font-weight: 600;
}
</style>
