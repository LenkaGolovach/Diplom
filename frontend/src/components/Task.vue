<template>
  <div class="task" @click="$emit('click', task)">
    <div class="task-content">
      <div class="task-header">
        <span class="task-name">{{ task.name }}</span>
        <button @click.stop="$emit('delete', task)" class="delete-button">×</button>
      </div>
      
      <div class="task-details">
        <!-- Отображение прогресса подзадач -->
        <div v-if="task.subtasks && task.subtasks.length > 0" class="subtask-progress">
          <span>{{ completedSubtasksCount }}/{{ task.subtasks.length }}</span>
          <div class="progress-bar-inline">
            <div class="progress-inline" :style="{ width: progress + '%' }"></div>
          </div>
        </div>

        <!-- Превью файлов -->
        <div v-if="task.attachments && task.attachments.length > 0" class="file-previews">
          <div 
            v-for="(attachment, index) in visibleAttachments" 
            :key="index" 
            class="file-preview-badge"
            :title="attachment.name" 
            @click.stop="downloadFile(attachment)"
          >
            <img v-if="isImage(attachment.file)" :src="attachment.url" alt="Preview">
            <span v-else class="file-ext">{{ getFileExtension(attachment.name) }}</span>
          </div>
          <div v-if="hiddenAttachmentsCount > 0" class="more-files">
            +{{ hiddenAttachmentsCount }}
          </div>
        </div>
      </div>
    </div>

    <div class="task-footer">
       <!-- Тег приоритета -->
      <div v-if="task.priority" :class="['priority-tag', `priority-${task.priority}`]">
        {{ priorityText }}
      </div>
      <!-- Аватарки участников -->
      <div class="participants-preview">
        <div 
          v-for="member in task.members.slice(0, 3)" 
          :key="member.email"
          class="participant-avatar"
          :title="member.email" 
        >
          <img :src="member.avatar || '/default-avatar.png'" class="avatar">
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
    completedSubtasksCount() {
       if (!this.task.subtasks || this.task.subtasks.length === 0) return 0;
       return this.task.subtasks.filter(s => s.completed).length;
    },
    visibleAttachments() {
      // Показываем до 4 превью
      return (this.task.attachments && this.task.attachments.slice(0, 4)) || [];
    },
    hiddenAttachmentsCount() {
      return Math.max((this.task.attachments && this.task.attachments.length || 0) - 4, 0);
    },
    isImage() {
      // Упрощенная проверка по расширению
      return filePath => {
        if (!filePath) return false;
        const ext = filePath.split('.').pop().toLowerCase();
        return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext);
      };
    },
    priorityText() {
      switch (this.task.priority) {
        case 'high': return 'Высокий';
        case 'medium': return 'Средний';
        case 'low': return 'Низкий';
        default: return '';
      }
    }
  },
  methods: {
    downloadFile(attachment) {
      event.stopPropagation();
      const link = document.createElement('a');
      link.href = attachment.url || attachment.file;
      link.download = attachment.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    getFileExtension(filename) {
      if (!filename) return '';
      const ext = filename.split('.').pop().toLowerCase();
      return ext.length > 4 ? ext.substring(0, 3) + '..' : ext;
    }
  }
};
</script>

<style scoped>
.task {
  background-color: white;
  border-radius: 10px; /* Слегка увеличили радиус */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* Более мягкая тень */
  padding: 16px; /* Увеличили отступы */
  margin: 12px 5px;
  cursor: pointer;
  transition: all 0.25s ease-in-out;
  display: flex;
  flex-direction: column;
  border: 1px solid #eef2f7; /* Тонкая граница */
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; /* Системный шрифт */
}

.task:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  border-color: #dde5f0;
}

.task-content {
  flex-grow: 1; /* Занимает доступное пространство */
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.task-name {
  font-weight: 600; /* Сделали чуть жирнее */
  font-size: 15px; /* Немного увеличили */
  color: #1e293b; /* Сделали темнее */
  line-height: 1.4;
  word-break: break-word;
  padding-right: 10px;
  flex: 1;
}

.delete-button {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 18px;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
  margin-top: -3px; /* Выравниваем по верху */
  opacity: 0.6;
}

.task:hover .delete-button {
  opacity: 1;
}

.delete-button:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  transform: rotate(90deg);
}

.task-details {
  margin-bottom: 12px; /* Отступ под деталями */
  display: flex;
  flex-direction: column;
  gap: 10px; /* Отступ между деталями */
  min-height: 30px; /* Минимальная высота, чтобы карточка не схлопывалась */
}

.subtask-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.progress-bar-inline {
  flex: 1;
  height: 5px;
  background: #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  margin-left: 4px;
}

.progress-inline {
  height: 100%;
  background: #60a5fa; /* Голубой цвет прогресса */
  transition: width 0.4s ease;
  border-radius: 10px;
}

.file-previews {
  display: flex;
  align-items: center;
  gap: 6px;
}

.file-preview-badge {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  text-transform: uppercase;
}

.file-preview-badge:hover {
  transform: scale(1.05);
  border-color: #cbd5e1;
}

.file-preview-badge img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 5px; /* Внутренний радиус */
}

.more-files {
  background: #e2e8f0;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12px;
  height: 26px;
  display: flex;
  align-items: center;
  color: #64748b;
  font-weight: 500;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto; /* Прижимаем футер к низу */
  padding-top: 12px; /* Отступ сверху */
  border-top: 1px solid #f1f5f9; /* Тонкий разделитель */
}

.priority-tag {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
}

.priority-tag.priority-high {
  background-color: #fee2e2; /* Светло-красный фон */
  color: #dc2626; /* Темно-красный текст */
}

.priority-tag.priority-medium {
  background-color: #ffedd5; /* Светло-оранжевый фон */
  color: #ea580c; /* Темно-оранжевый текст */
}

.priority-tag.priority-low {
  background-color: #dbeafe; /* Светло-синий фон */
  color: #2563eb; /* Темно-синий текст */
}

.participants-preview {
  display: flex;
  flex-direction: row-reverse; /* Аватарки накладываются слева направо */
}

.participant-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 2px solid white; /* Белая обводка */
  margin-left: -8px; /* Наложение аватарок */
  background-color: #e2e8f0; /* Фон для случая, если нет img */
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.participant-avatar:hover {
  transform: scale(1.1);
  z-index: 1;
}

.participant-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-participants {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background-color: #e2e8f0;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  border: 2px solid white;
  margin-left: -8px;
}

</style>
