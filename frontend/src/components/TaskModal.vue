<template>
  <div class="modal">
    <div class="modal-content">
      <!-- Заголовок задачи с возможностью редактирования -->
      <div class="task-header">
        <div
          v-if="!isEditingTitle"
          class="task-title"
          @dblclick="startEditingTitle"
        >
          {{ localTask.name || 'Новая задача' }}
        </div>
        <input
          v-else
          ref="titleInput"
          v-model="localTask.name"
          @blur="stopEditingTitle"
          @keyup.enter="stopEditingTitle"
          class="task-title-input"
          placeholder="Название задачи"
        />
      </div>

      <!-- Описание задачи -->
      <div class="form-group">
        <label>Описание:</label>
        <textarea
          v-model="localTask.description"
          placeholder="Введите описание задачи"
          class="description-input"
        ></textarea>
      </div>

      <!-- Прогресс-бар (только если есть подзадачи) -->
      <div v-if="hasSubtasks" class="progress-container">
        <div class="progress-bar">
          <div class="progress" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ progress }}% выполнено</div>
      </div>

      <!-- Кнопка добавления подзадачи -->
      <button @click="addSubtask" class="add-subtask-button">
        + Добавить подзадачу
      </button>

      <!-- Список подзадач -->
      <div class="subtasks">
        <div v-for="(subtask, index) in localTask.subtasks" :key="index" class="subtask">
          <input
            type="checkbox"
            v-model="subtask.completed"
            @change="updateProgress"
          />
          <div
            class="subtask-title"
            @dblclick="startEditingSubtask(index)"
          >
            <template v-if="!subtask.editing">
              {{ subtask.name }}
            </template>
            <input
              v-else
              v-model="subtask.name"
              @blur="stopEditingSubtask(index)"
              @keyup.enter="stopEditingSubtask(index)"
              class="subtask-input"
            />
          </div>
          <button @click="deleteSubtask(index)" class="delete-subtask-button">
            ×
          </button>
        </div>
      </div>

      <!-- Секция для прикрепленных файлов -->
      <div class="file-section">
        <label>Прикрепленные файлы:</label>
        <div class="file-list">
          <div v-for="(file, index) in localTask.files" :key="index" class="file-item">
            <div class="file-preview" @click="downloadFile(file)">
              <img v-if="isImage(file.type)" :src="file.url" class="thumbnail">
              <div v-else class="file-icon">
                <img src="/icons/file-icon.png" alt="Document Icon" class="file-icon-img">
              </div>
            </div>
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <button @click="removeFile(index)" class="delete-file">×</button>
            </div>
          </div>
        </div>
        
        <label class="file-upload">
          <input 
            ref="fileInput"
            type="file" 
            @change="handleFileUpload" 
            multiple
            class="file-input"
          >
          <span class="upload-button">+ Добавить файлы</span>
        </label>
      </div>

      <!-- Секция участников -->
      <div class="participants-section">
        <label>Участники:</label>
        <div class="participants-list">
          <div 
            v-for="member in localTask.members" 
            :key="member.email"
            class="participant"
          >
            <img 
              :src="member.avatar || '/default-avatar.png'" 
              class="avatar"
            >
            <span>{{ member.email }}</span>
          </div>
        </div>
        <button 
          @click="toggleParticipation"
          :class="['participation-btn', { 'joined': isParticipant }]"
          :disabled="!localTask.id"
        >
          {{ isParticipant ? 'Отказаться' : 'Присоединиться' }}
        </button>
      </div>

      <!-- GitHub интеграция -->
      <div class="github-section">
        <label>GitHub интеграция:</label>
        <div class="github-controls">
          <select v-model="selectedGitHubAction" class="github-action-select">
            <option value="">Выберите действие</option>
            <option value="track-commits">Отслеживать коммиты</option>
            <option value="repo-info">Информация о репозитории</option>
            <option value="view-prs">Просмотр Pull Requests</option>
          </select>

          <!-- Выбор репозитория -->
          <div v-if="selectedGitHubAction && !linkedRepo" class="github-content">
            <div class="repo-selection">
              <h4>Выберите репозиторий</h4>
              
              <!-- Вкладки -->
              <div class="repo-tabs">
                <button 
                  :class="['tab-btn', { active: activeTab === 'search' }]"
                  @click="activeTab = 'search'"
                >
                  Поиск
                </button>
                <button 
                  :class="['tab-btn', { active: activeTab === 'recent' }]"
                  @click="activeTab = 'recent'"
                >
                  Недавние
                </button>
                <button 
                  :class="['tab-btn', { active: activeTab === 'link' }]"
                  @click="activeTab = 'link'"
                >
                  Ссылка
                </button>
              </div>

              <!-- Поиск репозиториев -->
              <div v-if="activeTab === 'search'" class="tab-content">
                <div class="search-container">
                  <input 
                    v-model="githubSearchQuery" 
                    @input="searchGitHubRepos" 
                    placeholder="Поиск репозиториев..."
                    class="github-search-input"
                  >
                  <div v-if="searchResults.length" class="search-results">
                    <div 
                      v-for="repo in searchResults" 
                      :key="repo.id" 
                      class="repo-item"
                      @click="selectRepo(repo)"
                    >
                      <div class="repo-name">{{ repo.name }}</div>
                      <div class="repo-description">{{ repo.description }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Недавние репозитории -->
              <div v-if="activeTab === 'recent'" class="tab-content">
                <div v-if="recentRepos.length" class="recent-repos">
                  <div 
                    v-for="repo in recentRepos" 
                    :key="repo.id" 
                    class="repo-item"
                    @click="selectRepo(repo)"
                  >
                    <div class="repo-name">{{ repo.name }}</div>
                    <div class="repo-description">{{ repo.description }}</div>
                  </div>
                </div>
                <div v-else class="no-repos-message">
                  Нет недавно использованных репозиториев
                </div>
              </div>

              <!-- Ввод ссылки -->
              <div v-if="activeTab === 'link'" class="tab-content">
                <div class="link-repo-container">
                  <input 
                    v-model="repoUrl" 
                    placeholder="https://github.com/user/repo" 
                    class="repo-url-input"
                  >
                  <button @click="linkRepository" class="link-repo-btn">
                    Привязать
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Содержимое в зависимости от выбранного действия -->
          <div v-else-if="selectedGitHubAction && linkedRepo" class="github-content">
            <!-- Отслеживание коммитов -->
            <div v-if="selectedGitHubAction === 'track-commits'" class="action-content">
              <div class="repo-header">
                <div class="repo-info">
                  <span class="repo-name">{{ linkedRepo.name }}</span>
                  <button @click="changeRepo" class="change-repo-btn">
                    Сменить репозиторий
                  </button>
                </div>
                <button @click="refreshCommits" class="refresh-btn">
                  🔄 Обновить
                </button>
              </div>
              <div class="commits-list">
                <div v-if="commits && commits.length > 0">
                  <div 
                    v-for="commit in commits" 
                    :key="commit.sha" 
                    class="commit-item"
                    :class="{ 'error-commit': commit.sha.startsWith('error') }"
                  >
                    <div class="commit-header">
                      <img :src="commit.author.avatar_url" class="author-avatar">
                      <span class="author-name">{{ commit.author.name }}</span>
                      <a 
                        v-if="!commit.sha.startsWith('error')" 
                        :href="commit.html_url" 
                        target="_blank" 
                        class="commit-link"
                      >
                        <i class="external-icon">↗</i>
                      </a>
                    </div>
                    <div class="commit-message">{{ commit.message }}</div>
                    <div class="commit-date">{{ commit.author.date }}</div>
                  </div>
                </div>
                <div v-else class="empty-commits">
                  <p>Коммиты не найдены. Попробуйте обновить.</p>
                  <div v-if="commitsDebug" class="debug-info">
                    <pre>{{ JSON.stringify(commitsDebug, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <!-- Pull Requests -->
            <div v-if="selectedGitHubAction === 'view-prs'" class="action-content">
              <div class="repo-header">
                <div class="repo-info">
                  <span class="repo-name">{{ linkedRepo.name }}</span>
                  <button @click="changeRepo" class="change-repo-btn">
                    Сменить репозиторий
                  </button>
                </div>
                <button @click="refreshPRs" class="refresh-btn">
                  🔄 Обновить
                </button>
              </div>
              <div class="prs-list">
                <div 
                  v-for="pr in pullRequests" 
                  :key="pr.id" 
                  class="pr-item"
                >
                  <div class="pr-title">{{ pr.title }}</div>
                  <div class="pr-info">
                    <span class="pr-author">{{ pr.user.login }}</span>
                    <span class="pr-status" :class="pr.state">{{ pr.state }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Информация о репозитории (новая секция) -->
            <div v-if="selectedGitHubAction === 'repo-info'" class="action-content">
              <div class="repo-header">
                <div class="repo-info">
                  <span class="repo-name">{{ linkedRepo.name }}</span>
                  <button @click="changeRepo" class="change-repo-btn">
                    Сменить репозиторий
                  </button>
                </div>
                <button @click="refreshRepoInfo" class="refresh-btn">
                  🔄 Обновить
                </button>
              </div>
              <div class="repo-details">
                <div class="repo-detail-item">
                  <div class="detail-label">Владелец:</div>
                  <div class="detail-value">{{ repoDetails.owner }}</div>
                </div>
                <div class="repo-detail-item">
                  <div class="detail-label">Дата создания:</div>
                  <div class="detail-value">{{ repoDetails.created_at || 'Н/Д' }}</div>
                </div>
                <div class="repo-detail-item">
                  <div class="detail-label">Последнее обновление:</div>
                  <div class="detail-value">{{ repoDetails.updated_at || 'Н/Д' }}</div>
                </div>
                <div class="repo-detail-item">
                  <div class="detail-label">Звёзд:</div>
                  <div class="detail-value">{{ repoDetails.stars || 0 }}</div>
                </div>
                <div class="repo-detail-item">
                  <div class="detail-label">Форков:</div>
                  <div class="detail-value">{{ repoDetails.forks || 0 }}</div>
                </div>
                <div class="repo-url-item">
                  <div class="detail-label">URL:</div>
                  <a :href="repoDetails.html_url" target="_blank" class="repo-link">
                    {{ repoDetails.html_url }} <i class="external-icon">↗</i>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопки управления -->
      <div class="actions">
        <button @click="saveTask" class="save-button">Сохранить</button>
        <button @click="closeModal" class="close-button">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import GitHubService from '@/services/GitHubService';

export default {
  props: {
    task: Object,
  },
  data() {
    return {
      isEditingTitle: false,
      localTask: {
        id: this.task.id,
        name: this.task.name || '',
        description: this.task.description || '',
        subtasks: Array.isArray(this.task.subtasks) ? [...this.task.subtasks] : [],
        files: Array.isArray(this.task.attachments) ? [...this.task.attachments] : [],
        column: this.task.column,
        members: Array.isArray(this.task.members) ? [...this.task.members] : [],
      },
      uploadedFiles: [],
      deletedFileIds: [],
      isParticipant: false,
      selectedGitHubAction: '',
      githubSearchQuery: '',
      searchResults: [],
      linkedRepo: null,
      commits: [],
      pullRequests: [],
      repoUrl: '',
      activeTab: 'search',
      recentRepos: [],
      commitsDebug: null,
      repoDetails: {},
    };
  },
  computed: {
    progress() {
      if (!this.hasSubtasks) return 0;
      const completed = this.localTask.subtasks.filter(s => s.completed).length;
      return Math.round((completed / this.localTask.subtasks.length) * 100);
    },
    hasSubtasks() {
      return this.localTask.subtasks && this.localTask.subtasks.length > 0;
    },
  },
  methods: {
    startEditingTitle() {
      this.isEditingTitle = true;
      this.$nextTick(() => {
        this.$refs.titleInput.focus();
      });
    },
    stopEditingTitle() {
      this.isEditingTitle = false;
    },
    startEditingSubtask(index) {
      // Прямое изменение свойства с реактивным обновлением
      this.localTask.subtasks[index].editing = true;
      this.$nextTick(() => {
        const inputs = this.$el.querySelectorAll('.subtask-input');
        if (inputs[index]) inputs[index].focus();
      });
    },
    stopEditingSubtask(index) {
      this.localTask.subtasks[index].editing = false;
    },
    addSubtask() {
      if (!this.localTask.subtasks) {
        this.localTask.subtasks = [];
      }
      this.localTask.subtasks.push({
        name: 'Новая подзадача',
        completed: false,
        editing: false
      });
      
      // Обновляем высоту контейнера подзадач
      this.$nextTick(() => {
        this.adjustSubtasksHeight();
        
        // Прокручиваем к последней добавленной подзадаче
        this.scrollToLastSubtask();
      });
    },
    scrollToLastSubtask() {
      setTimeout(() => {
        const subtasksEl = this.$el.querySelector('.subtasks');
        if (!subtasksEl) return;
        
        // Прокручиваем контейнер к самому низу
        subtasksEl.scrollTop = subtasksEl.scrollHeight;
      }, 50); // Небольшая задержка для надежности
    },
    deleteSubtask(index) {
      this.localTask.subtasks.splice(index, 1);
      
      // Обновляем высоту контейнера подзадач после удаления
      this.$nextTick(() => {
        this.adjustSubtasksHeight();
      });
    },
    adjustSubtasksHeight() {
      const subtasksEl = this.$el.querySelector('.subtasks');
      if (!subtasksEl) return;
      
      const subtaskCount = this.localTask.subtasks ? this.localTask.subtasks.length : 0;
      
      // Простая логика: для пустого списка - фиксированная высота, 
      // для непустого - автоматическая до максимума
      if (subtaskCount === 0) {
        // Если нет подзадач, устанавливаем минимальную высоту
        subtasksEl.style.height = '160px'; // Увеличенная фиксированная высота для пустого состояния
      } else {
        // Для любого количества подзадач - убираем явную высоту,
        // позволяя контейнеру расти до max-height из CSS
        subtasksEl.style.height = 'auto';
      }
    },
    updateProgress() {
      // Обновление прогресса происходит автоматически через computed свойство
    },
    closeModal() {
      this.$emit('close');
    },
    isImage(type) {
      return type && type.startsWith('image/');
    },
    handleFileUpload(e) {
      const files = Array.from(e.target.files);
      
      // Проверяем наличие файлов
      if (!files || files.length === 0) return;
      
      // Сохраняем файлы для отправки на сервер
      this.uploadedFiles = [...this.uploadedFiles, ...files];
      
      // Отображаем превью файлов
      files.forEach(file => {
        const reader = new FileReader();
        
        reader.onload = (e) => {
          if (!this.localTask.files) {
            this.localTask.files = [];
          }
          
          this.localTask.files.push({
            name: file.name,
            type: file.type,
            url: e.target.result,
            isNew: true // Флаг для новых файлов
          });
        };
        
        reader.readAsDataURL(file);
      });
      
      // Сбрасываем значение инпута
      this.$refs.fileInput.value = '';
    },
    async saveTask() {
      try {
        const formData = new FormData();
        formData.append('name', this.localTask.name);
        formData.append('description', this.localTask.description || '');
        
        const columnId = this.localTask.column instanceof Object 
          ? this.localTask.column.id 
          : this.localTask.column;
        
        formData.append('column', columnId);
        
        // Подзадачи - очищаем поле editing перед отправкой
        if (this.localTask.subtasks && this.localTask.subtasks.length > 0) {
          const cleanSubtasks = this.localTask.subtasks.map(s => ({
            id: s.id,
            name: s.name,
            completed: s.completed
          }));
          formData.append('subtasks', JSON.stringify(cleanSubtasks));
        }
        
        // Новые файлы
        if (this.uploadedFiles.length > 0) {
          this.uploadedFiles.forEach(file => {
            formData.append('attachments', file);
          });
        }

        if (this.deletedFileIds.length > 0) {
          this.deletedFileIds.forEach(id => {
              formData.append('deleted_files', id.toString());
          });
        }
        
        const config = {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        };
        
        let response;
        if (this.localTask.id) {
          response = await axios.patch(`/api/tasks/${this.localTask.id}/`, formData, config);
        } else {
          response = await axios.post('/api/tasks/', formData, config);
        }

        // Обновляем локальные данные задачи после сохранения
        this.localTask = response.data;

        // Проверяем участие пользователя в задаче
        await this.checkParticipation();
        
        this.$emit('saveTask', response.data);
        this.closeModal();
      } catch (error) {
        console.error('Ошибка сохранения задачи:', error);
        alert(`Ошибка: ${(error.response && error.response.data) || error.message}`);
      }
    },
    removeFile(index) {
      if (this.localTask.files && this.localTask.files.length > index) {
        const file = this.localTask.files[index];
        if (file.id) {
          // If the file has an ID, it's from the server, so add it to deletedFileIds
          this.deletedFileIds.push(file.id);
        }
        this.localTask.files.splice(index, 1);
      }
    },
    downloadFile(file) {
      // Создаем временную ссылку для скачивания
      const link = document.createElement('a');
      link.href = file.url;
      link.download = file.name; // Имя файла при скачивании
      document.body.appendChild(link);
      link.click(); // Инициируем скачивание
      document.body.removeChild(link); // Удаляем ссылку после скачивания
    },
    async checkParticipation() {
      if (!this.localTask.id) {
        this.isParticipant = false;
        return;
      }
      try {
        const response = await axios.get(`/api/tasks/${this.localTask.id}/members/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        this.isParticipant = response.data.some(m => m.email === this.$store.state.user.email);
      } catch (error) {
        console.error('Ошибка проверки участия:', error);
      }
    },
    async toggleParticipation() {
      if (!this.localTask.id) {
        alert("Сначала сохраните задачу, чтобы присоединиться к ней.");
        return;
      }
      try {
        if (this.isParticipant) {
          await axios.delete(`/api/tasks/${this.localTask.id}/members/${this.$store.state.user.id}/`, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
        } else {
          await axios.post(`/api/tasks/${this.localTask.id}/members/`, {}, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
        }
        await this.fetchTaskData();
        await this.checkParticipation();
      } catch (error) {
        console.error('Ошибка изменения статуса участия:', error);
      }
    },
    async fetchTaskData() {
      if (!this.localTask.id) return;

      try {
        const response = await axios.get(`/api/tasks/${this.localTask.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.localTask = {
          ...response.data,
          // Map attachments to files to maintain consistency
          files: response.data.attachments || []
        };
        
        // Обновляем высоту контейнера подзадач после загрузки данных
        this.$nextTick(() => {
          this.adjustSubtasksHeight();
        });
      } catch (error) {
        console.error('Ошибка загрузки данных задачи:', error);
      }
    },
    async searchGitHubRepos() {
      if (!this.githubSearchQuery.trim()) {
        this.searchResults = [];
        return;
      }
      
      try {
        this.searchResults = await GitHubService.searchRepositories(this.githubSearchQuery);
      } catch (error) {
        console.error('Ошибка поиска репозиториев:', error);
        this.searchResults = [];
      }
    },
    async selectRepo(repo) {
      this.linkedRepo = repo;
      this.searchResults = [];
      this.githubSearchQuery = '';
      await this.refreshCommits();
    },
    async refreshCommits() {
      if (!this.linkedRepo) return;
      try {
        console.log('Запрос коммитов для', this.linkedRepo.full_name);
        this.commitsDebug = { status: 'loading' };
        
        // Очищаем текущие коммиты перед загрузкой новых
        this.commits = [];
        
        // Загружаем коммиты
        const commits = await GitHubService.getCommits(this.linkedRepo.full_name);
        console.log('Полученные коммиты:', commits);
        
        // Проверяем, что данные пришли
        if (!commits || !Array.isArray(commits)) {
          console.error('Неверный формат данных о коммитах:', commits);
          this.commitsDebug = { 
            status: 'error', 
            message: 'Неверный формат данных', 
            data: commits 
          };
          return;
        }
        
        this.commits = commits;
        this.commitsDebug = { 
          status: 'success', 
          count: commits.length 
        };
      } catch (error) {
        console.error('Ошибка загрузки коммитов:', error);
        this.commitsDebug = { 
          status: 'error', 
          message: error.message, 
          stack: error.stack
        };
      }
    },
    async linkRepository() {
      if (!this.repoUrl) {
        alert('Введите URL репозитория');
        return;
      }

      try {
        // Парсим URL репозитория
        const { fullName } = GitHubService.parseRepositoryUrl(this.repoUrl);
        
        // Получаем информацию о репозитории
        const repoData = await GitHubService.getRepository(fullName);
        
        // Привязываем репозиторий к задаче
        await GitHubService.linkRepository(repoData.full_name, this.localTask.id);
        
        this.linkedRepo = repoData;
        this.repoUrl = '';
        
        // Обновляем список недавних репозиториев
        await this.fetchRecentRepos();
      } catch (error) {
        console.error('Ошибка привязки репозитория:', error);
        if (error.message === 'Неверный формат URL репозитория GitHub') {
          alert(error.message);
        } else if (error.response && error.response.status === 404) {
          alert('Репозиторий не найден. Проверьте URL и права доступа.');
        } else {
          alert('Ошибка при привязке репозитория. Попробуйте позже.');
        }
      }
    },
    async refreshPRs() {
      if (!this.linkedRepo) return;
      try {
        this.pullRequests = await GitHubService.getPullRequests(this.linkedRepo.full_name);
      } catch (error) {
        console.error('Ошибка загрузки Pull Requests:', error);
      }
    },
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    },
    changeRepo() {
      this.linkedRepo = null;
    },
    async fetchRecentRepos() {
      try {
        this.recentRepos = await GitHubService.getRecentRepositories();
      } catch (error) {
        console.error('Ошибка загрузки недавних репозиториев:', error);
      }
    },
    async refreshRepoInfo() {
      if (!this.linkedRepo) return;
      try {
        this.repoDetails = await GitHubService.getRepositoryInfo(this.linkedRepo.full_name);
      } catch (error) {
        console.error('Ошибка загрузки информации о репозитории:', error);
      }
    },
  },
  watch: {
    selectedGitHubAction(newAction) {
      if (newAction && !this.linkedRepo) {
        this.fetchRecentRepos();
      } else if (newAction === 'track-commits' && this.linkedRepo) {
        this.refreshCommits();
      } else if (newAction === 'view-prs' && this.linkedRepo) {
        this.refreshPRs();
      } else if (newAction === 'repo-info' && this.linkedRepo) {
        this.refreshRepoInfo();
      }
    },
    'localTask.subtasks': {
      handler() {
        this.$nextTick(() => {
          this.adjustSubtasksHeight();
        });
      },
      deep: true
    }
  },
  mounted() {
    if (this.localTask.id) {
      this.fetchTaskData();
      this.checkParticipation();
    }
    
    // Инициализируем высоту контейнера подзадач при загрузке
    this.$nextTick(() => {
      this.adjustSubtasksHeight();
    });
  }
};
</script>

<style scoped>
/* Стилизация полос прокрутки */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
  padding: 20px;
  box-sizing: border-box;
}

.modal-content {
  background: white;
  padding: 20px 20px 0 20px; /* Убираем нижний padding */
  border-radius: 8px;
  width: 500px;
  max-width: 90%; 
  max-height: 90vh;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 1002;
  display: flex;
  flex-direction: column;
  position: relative;
}

.task-header {
  margin-bottom: 20px;
  position: sticky;
  top: 0;
  background: white;
  padding: 5px 0;
  z-index: 10;
  border-bottom: 1px solid #f0f0f0;
}

.task-title {
  font-size: 1.5em;
  font-weight: bold;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
}

.task-title:hover {
  background: #f0f0f0;
}

.task-title-input {
  font-size: 1.5em;
  font-weight: bold;
  width: 100%;
  padding: 8px;
  border: 2px solid #0079bf;
  border-radius: 4px;
  margin-bottom: 15px;
  margin-right: 40px;
}

.description-input {
  width: 100%;
  min-height: 100px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 15px;
  margin-right: 40px;
}

.add-subtask-button {
  width: 100%;
  padding: 8px;
  background: #f0f0f0;
  border: none;
  border-radius: 4px;
  margin: 10px 0;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.add-subtask-button:hover {
  background: #e0e0e0;
}

.subtasks {
  margin: 15px 0;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 5px 10px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  min-height: 150px; /* Увеличенная минимальная высота */
  /* max-height: 1600px; 400px * 4 = 1600px */
  overflow-y: auto;
}

/* Улучшаем стиль скроллбара для контейнера подзадач */
.subtasks::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.subtasks::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 3px;
}

.subtasks::-webkit-scrollbar-thumb:hover {
  background-color: #aaa;
}

.subtasks::-webkit-scrollbar-track {
  background-color: #f0f0f0;
  border-radius: 3px;
}

.subtask {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
  padding: 6px 4px;
  min-height: 32px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.subtask:hover {
  background-color: #f5f5f5;
}

/* Подсветка при редактировании */
.subtask:has(.subtask-input) {
  background-color: #f0f7ff;
  border: 1px dashed #0079bf;
  padding: 5px 3px; /* Компенсируем border */
}

/* Стиль для чекбокса */
.subtask input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Стиль для названия подзадачи */
.subtask-title {
  flex: 1;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 3px;
  transition: background-color 0.2s ease;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtask-title:hover {
  background-color: #e9e9e9;
}

/* Стиль для задач, отмеченных как выполненные */
.subtask input[type="checkbox"]:checked + .subtask-title {
  text-decoration: line-through;
  color: #888;
}

/* Стиль для кнопки удаления подзадачи */
.delete-subtask-button {
  background: #ff6b6b;
  border: none;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 4px;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.delete-subtask-button:hover {
  opacity: 1;
}

.form-group {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.progress-container {
  margin: 15px 0;
  padding-bottom: 15px;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #76c7c0;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  font-size: 0.9em;
  color: #666;
  margin-top: 5px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 15px 20px;
  border-top: 1px solid #f0f0f0;
  margin: 20px -20px 0 -20px; /* Негативные отступы по бокам */
  border-radius: 0 0 8px 8px;
  z-index: 20;
}

.save-button {
  background: #76c7c0;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.close-button {
  background: #f0f0f0;
  border: 1px solid #ccc;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.file-section {
  margin: 15px 0;
  padding: 15px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 5px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-preview {
  width: 40px;
  height: 40px;
  margin-right: 12px;
  cursor: pointer;
}

.thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.file-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 4px;
}

.file-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  font-size: 0.9em;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-file {
  background: none;
  border: none;
  color: #ff6b6b;
  cursor: pointer;
  font-size: 1.2em;
  padding: 0 5px;
}

.file-upload {
  display: block;
  margin-top: 10px;
}

.file-input {
  display: none;
}

.upload-button {
  background: #f0f0f0;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-block;
  transition: background 0.3s;
}

.upload-button:hover {
  background: #e0e0e0;
}

.file-icon-img {
  width: 24px; /* Размер иконки */
  height: 24px;
  object-fit: contain; /* Сохраняет пропорции */
}

.participants-section {
  margin: 15px 0;
  padding: 15px 0;
  border-bottom: 1px solid #f0f0f0;
}

.participants-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}

.participant {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px;
  background: #f0f0f0;
  border-radius: 15px;
}

.avatar {
  width: 25px;
  height: 25px;
  border-radius: 50%;
}

.participation-btn {
  padding: 8px 15px;
  background: #0079bf;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.participation-btn.joined {
  background: #eb5a46;
}

.participation-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.github-section {
  margin-top: 20px;
  padding: 15px;
  background: #f6f8fa;
  border-radius: 8px;
  border: 1px solid #e1e4e8;
  margin-bottom: 20px; /* Уменьшаем отступ, так как кнопки теперь sticky */
}

.github-controls {
  margin-top: 10px;
}

.github-action-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  margin-bottom: 15px;
}

.github-content {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 15px;
  margin-top: 10px;
  max-height: 300px; /* Чуть уменьшаем высоту */
  overflow-y: auto;
  overflow-x: hidden;
}

.search-container {
  position: relative;
}

.github-search-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 14px;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.repo-item {
  padding: 10px;
  border-bottom: 1px solid #e1e4e8;
  cursor: pointer;
}

.repo-item:hover {
  background-color: #f6f8fa;
}

.repo-name {
  font-weight: 600;
  color: #0366d6;
}

.repo-description {
  font-size: 12px;
  color: #586069;
  margin-top: 4px;
}

.commits-container, .prs-container {
  max-height: 400px;
  overflow-y: auto;
}

.commit-item {
  padding: 12px;
  border-bottom: 1px solid #e1e4e8;
  transition: background-color 0.2s;
}

.commit-item:hover {
  background-color: #f6f8fa;
}

.commit-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.author-name {
  font-weight: 600;
  color: #24292e;
}

.commit-message {
  margin-top: 6px;
  margin-left: 32px;
  color: #24292e;
  font-weight: 500;
}

.commit-date {
  font-size: 12px;
  color: #586069;
  margin-top: 4px;
  margin-left: 32px;
}

.repo-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.refresh-btn {
  padding: 4px 8px;
  background: #f6f8fa;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  cursor: pointer;
}

.refresh-btn:hover {
  background: #e1e4e8;
}

.link-repo-container {
  display: flex;
  gap: 10px;
}

.repo-url-input {
  flex: 1;
  padding: 8px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
}

.link-repo-btn {
  padding: 8px 16px;
  background: #2ea44f;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.link-repo-btn:hover {
  background: #2c974b;
}

.pr-status {
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.pr-status.open {
  background: #2ea44f33;
  color: #22863a;
}

.pr-status.closed {
  background: #d73a4933;
  color: #cb2431;
}

.no-repo-message {
  text-align: center;
  color: #586069;
  padding: 20px;
}

.repo-selection {
  padding: 15px;
}

.repo-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  border-bottom: 1px solid #e1e4e8;
  padding-bottom: 10px;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  color: #24292e;
}

.tab-btn.active {
  background: #0366d6;
  color: white;
  border-color: #0366d6;
}

.tab-content {
  margin-top: 15px;
}

.recent-repos {
  max-height: 300px;
  overflow-y: auto;
}

.no-repos-message {
  text-align: center;
  color: #586069;
  padding: 20px;
}

.repo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.change-repo-btn {
  padding: 4px 8px;
  background: #f6f8fa;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #24292e;
}

.change-repo-btn:hover {
  background: #e1e4e8;
}

.action-content {
  margin-top: 10px;
}

.empty-commits {
  text-align: center;
  padding: 20px;
  background-color: #f8f8f8;
  border-radius: 6px;
  margin-top: 10px;
}

.debug-info {
  margin-top: 10px;
  padding: 10px;
  background: #f6f8fa;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}

.commit-link {
  margin-left: auto;
  color: #0366d6;
  text-decoration: none;
}

.external-icon {
  font-style: normal;
}

.error-commit {
  background-color: #ffe8e8;
  border-left: 3px solid #f78166;
}

.pr-item {
  padding: 10px;
  border-bottom: 1px solid #e1e4e8;
}

.pr-item:hover {
  background-color: #f6f8fa;
}

.repo-details {
  margin-top: 10px;
  overflow-y: auto;
  padding: 5px;
}

.repo-detail-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.detail-label {
  font-weight: 600;
  color: #24292e;
  width: 150px;
  flex-shrink: 0;
}

.detail-value {
  color: #586069;
  word-break: break-word;
}

.repo-url-item {
  margin-top: 16px;
  display: flex;
  align-items: flex-start;
}

.repo-link {
  color: #0366d6;
  text-decoration: none;
  word-break: break-word;
}

.commits-list, .prs-list {
  max-height: 220px; /* Уменьшаем высоту списков */
  overflow-y: auto;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  padding: 5px;
  margin-top: 10px;
}

/* Для всех ролловеров внутри модального окна добавляем скрытие горизонтальной прокрутки */
.modal-content *::-webkit-scrollbar-corner {
  background: transparent;
}

/* Кнопки в самом низу */
.modal-content::after {
  content: '';
  display: block;
  height: 20px; /* Дополнительное пространство внизу */
}

/* Добавляем стиль для прокрутки списка подзадач */
.subtasks::-webkit-scrollbar {
  width: 6px;
}

.subtasks::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 3px;
}

.subtasks::-webkit-scrollbar-track {
  background-color: #f0f0f0;
  border-radius: 3px;
}

.subtask-input {
  flex: 1;
  padding: 4px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.subtask:last-child {
  margin-bottom: 0; /* Убираем отступ у последней подзадачи */
}

/* Стиль для пустого списка задач */
.subtasks:empty::before {
  content: 'Нет подзадач';
  font-style: italic;
  color: #999;
  align-self: center;
  padding: 0;
  margin: auto; /* Центрирование по вертикали */
  font-size: 16px; /* Увеличиваем размер шрифта */
}
</style>