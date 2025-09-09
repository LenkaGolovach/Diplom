<template>
  <div class="modal">
    <div class="modal-content">
      <!-- Боковые вкладки -->
      <div class="sticky-tabs">
        <div 
          v-for="(tab, index) in tabs" 
          :key="index"
          :class="['tab', `color-${index}`, { 'active': activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <img :src="tab.icon" class="tab-icon" alt="">
        </div>
      </div>
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

      <!-- Основное содержимое с вкладками -->
      <div class="modal-body-with-tabs">

        <!-- Контент вкладок -->
        <div class="tab-content">
          <!-- Вкладка "Общее" -->
          <div v-if="activeTab === 'general'" class="tab-pane">
            <!-- Описание задачи -->
            <div class="form-group">
              <label class="description-label">
                Описание:
                <img
                  src="/icons/edit-icon.png"
                  alt="Редактировать"
                  class="edit-icon"
                  @click.stop="startEditingDescription"
                />
              </label>

              <!-- Просмотр Markdown -->
              <div
                v-if="!isEditingDescription"
                class="description-preview"
                v-html="renderedDescription"
                @dblclick="startEditingDescription"
              ></div>

              <!-- Режим редактирования -->
              <textarea
                v-else
                ref="descriptionTextarea"
                v-model="localTask.description"
                @blur="stopEditingDescription"
                @keyup.ctrl.enter="stopEditingDescription"
                placeholder="Введите описание задачи"
                class="description-input"
              ></textarea>
            </div>

            <!-- Приоритет задачи -->
            <div class="form-group">
              <label>Приоритет:</label>
              <select
                v-model="localTask.priority"
                class="form-control"
              >
                <option value="high">Высокий</option>
                <option value="medium">Средний</option>
                <option value="low">Низкий</option>
              </select>
            </div>

            <!-- Срок выполнения задачи -->
            <div class="form-group due-date-group">
              <label>Срок выполнения:</label>
              <input
                type="date"
                v-model="localTask.due_date"
                :min="localTask.created_at && formatForInput(localTask.created_at)"
                class="form-control due-date-input"
              />
            </div>

            <!-- Прогресс-бар (только если есть подзадачи) -->
            <div v-if="hasSubtasks" class="progress-container">
              <div class="progress-bar">
                <div class="progress" :style="{ width: progress + '%' }"></div>
              </div>
              <div class="progress-text">{{ progress }}% выполнено</div>
            </div>

            <!-- Подзадачи -->
            <div class="subtask-add-form">
              <input 
                v-model="newSubtaskName" 
                placeholder="Введите название подзадачи" 
                class="subtask-name-input"
                @keyup.enter="addSubtaskWithName"
              />
              <button @click="addSubtaskWithName" class="add-subtask-button">
                + Добавить подзадачу
              </button>
            </div>

            <div class="subtasks">
              <div v-for="(subtask, index) in localTask.subtasks" :key="index" class="subtask">
                <input
                  type="checkbox"
                  v-model="subtask.completed"
                  @change="updateProgress(index)"
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
                    ref="subtaskInputs"
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

            <!-- Прикрепленные файлы -->
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
          </div>

          <!-- Вкладка "Участники" -->
          <div v-if="activeTab === 'members'" class="tab-pane">
            <div class="participants-section">
              <label>Участники:</label>
              <div class="participants-list">
                <div
                  v-for="member in localTask.members"
                  :key="member.id"
                  class="participant"
                >
                  <img :src="member.avatar || '/default-avatar.png'" class="avatar">
                  <span>{{ displayName(member) }}</span>
                  <button
                    v-if="isOwner"
                    @click="removeTaskMember(member)"
                    class="remove-member-btn"
                  >×</button>
                </div>
              </div>

              <!-- Кнопка «Присоединиться/Отказаться» для самих участников -->
              <button 
                v-if="localTask.id"
                @click="toggleParticipation"
                :class="['participation-btn', { 'joined': isParticipant }]"
                :disabled="!localTask.id"
              >
                {{ isParticipant ? 'Отказаться' : 'Присоединиться' }}
              </button>

              <!-- Секция добавления новых участников -->
              <div v-if="isOwner" class="assign-participant">
                <div class="custom-dropdown">
                  <!-- Нажатие только на selected открывает/закрывает список -->
                  <div class="selected" @click="openDropdown = !openDropdown">
                    {{ newMemberId
                        ? availableMembersMap[newMemberId].email
                        : 'Выберите пользователя…' }}
                    <span class="arrow" :class="{ open: openDropdown }">▾</span>
                  </div>

                  <!-- сам список, клики в нём не всплывают наружу -->
                  <ul v-if="openDropdown" class="dropdown-list">
                    <li
                      v-for="user in availableMembers"
                      :key="user.user_id"
                      class="dropdown-item"
                      @click.stop="selectMember(user.user_id)"
                    >
                      <img :src="user.avatar" class="item-avatar" />
                      {{ displayName(user) }}
                    </li>
                  </ul>
                </div>

                <button
                  :disabled="!newMemberId"
                  @click="assignTaskMember"
                  class="assign-btn"
                >
                  Назначить участника
                </button>
              </div>
            </div>
          </div>

          <!-- Вкладка "Обсуждение" -->
          <div v-if="activeTab === 'discussion'" class="tab-pane">
            <DiscussionChat v-if="localTask.id" :task-id="localTask.id" />
          </div>

          <!-- Вкладка "История" -->
          <div v-if="activeTab === 'history'" class="tab-pane history-pane">
            <div v-if="historyLog.length === 0" class="no-history">
              Нет истории действий
            </div>
            <ul v-else class="history-list">
              <li v-for="(item, i) in historyLog" :key="i" class="history-item">
                <div class="history-marker"></div>
                <div class="history-content">
                  <div class="history-header">
                    <span class="history-user">{{ displayName({ email: item.user }) }}</span>
                    <span class="history-ts">{{ formatTs(item.ts) }}</span>
                  </div>
                  <div class="history-action">{{ item.action }}</div>
                </div>
              </li>
            </ul>
          </div>

          <!-- Вкладка "GitHub" -->
          <div v-if="activeTab === 'github'" class="tab-pane">
            <div class="github-section">
              <div class="github-header">
                <div class="github-logo">
                  <img src="/icons/github-icon.png" alt="GitHub" class="github-logo-img">
                  <h3>GitHub интеграция</h3>
                </div>
                <p class="github-description">Привяжите GitHub репозиторий к задаче, чтобы отслеживать коммиты, просматривать Pull Requests и получать информацию о репозитории.</p>
              </div>

              <div class="github-action-wrapper">
                <label for="github-action">Выберите действие:</label>
                <select 
                  id="github-action" 
                  v-model="selectedGitHubAction" 
                  class="github-action-select"
                >
                  <option value="">Выберите действие</option>
                  <option value="track-commits">Отслеживать коммиты</option>
                  <option value="repo-info">Информация о репозитории</option>
                  <option value="view-prs">Просмотр Pull Requests</option>
                </select>
              </div>

              <!-- Выбор репозитория -->
              <div v-if="selectedGitHubAction && !linkedRepo" class="github-content-wrapper">
                <div class="repo-selection-container">
                  <h4 class="repo-selection-title">Выберите репозиторий</h4>
                  
                  <!-- Вкладки -->
                  <div class="repo-tabs">
                    <button 
                     :class="['tab-btn', { active: githubActiveTab === 'search' }]"
                     @click="githubActiveTab = 'search'"
                    >
                      <i class="fas fa-search"></i> Поиск
                    </button>
                    <button 
                     :class="['tab-btn', { active: githubActiveTab === 'recent' }]"
                     @click="githubActiveTab = 'recent'"
                    >
                      <i class="fas fa-history"></i> Недавние
                    </button>
                    <button 
                     :class="['tab-btn', { active: githubActiveTab === 'link' }]"
                     @click="githubActiveTab = 'link'"
                    >
                      <i class="fas fa-link"></i> Ссылка
                    </button>
                  </div>

                  <!-- Поиск репозиториев -->
                  <div v-if="githubActiveTab === 'search'" class="repo-tab-content">
                    <div class="search-container">
                      <div class="search-input-wrapper">
                        <i class="fas fa-search search-icon"></i>
                        <input 
                          v-model="githubSearchQuery" 
                          @input="searchGitHubRepos" 
                          placeholder="Поиск репозиториев..."
                          class="github-search-input"
                          autocomplete="off"
                        >
                      </div>
                      <div v-if="isSearching" class="search-loader">
                        <div class="loader"></div>
                      </div>
                      <div v-else-if="searchResults.length" class="search-results">
                        <div 
                          v-for="repo in searchResults" 
                          :key="repo.id" 
                          class="repo-item"
                          @click="selectRepo(repo)"
                        >
                          <div class="repo-item-header">
                            <i class="fas fa-book-open repo-icon"></i>
                            <div class="repo-name">{{ repo.name }}</div>
                          </div>
                          <div class="repo-description">{{ repo.description || 'Нет описания' }}</div>
                        </div>
                      </div>
                      <div v-else-if="githubSearchQuery && !searchResults.length" class="no-results">
                        <i class="fas fa-search-minus"></i>
                        <p>Репозитории не найдены. Попробуйте другой запрос.</p>
                      </div>
                    </div>
                  </div>

                  <!-- Недавние репозитории -->
                  <div v-if="githubActiveTab === 'recent'" class="repo-tab-content">
                    <div v-if="recentRepos.length" class="recent-repos">
                      <div 
                        v-for="repo in recentRepos" 
                        :key="repo.id" 
                        class="repo-item"
                        @click="selectRepo(repo)"
                      >
                        <div class="repo-item-header">
                          <i class="fas fa-history repo-icon"></i>
                          <div class="repo-name">{{ repo.name }}</div>
                        </div>
                        <div class="repo-description">{{ repo.description || 'Нет описания' }}</div>
                      </div>
                    </div>
                    <div v-else class="no-repos-message">
                      <i class="fas fa-exclamation-circle"></i>
                      <p>Нет недавно использованных репозиториев</p>
                    </div>
                  </div>

                  <!-- Ввод ссылки -->
                  <div v-if="githubActiveTab === 'link'" class="repo-tab-content">
                    <div class="link-repo-container">
                      <div class="link-input-wrapper">
                        <i class="fas fa-link link-icon"></i>
                        <input 
                          v-model="repoUrl" 
                          placeholder="https://github.com/user/repo" 
                          class="repo-url-input"
                          autocomplete="off"
                        >
                      </div>
                      <p class="link-help-text">
                        Введите полный URL GitHub репозитория или формат username/repository
                      </p>
                      <button @click="linkRepository" class="link-repo-btn" :disabled="!repoUrl.trim()">
                        <i class="fas fa-plus"></i> Привязать репозиторий
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Содержимое в зависимости от выбранного действия -->
              <div v-else-if="selectedGitHubAction && linkedRepo" class="github-content-wrapper">
                <!-- Отслеживание коммитов -->
                <div v-if="selectedGitHubAction === 'track-commits'" class="action-content">
                  <div class="repo-header">
                    <div class="repo-info">
                      <i class="fas fa-book repo-icon"></i>
                      <div class="repo-name-container">
                        <span class="repo-owner">{{ linkedRepo.full_name.split('/')[0] }}</span>
                        <span class="repo-name-divider">/</span>
                        <span class="repo-name">{{ linkedRepo.name }}</span>
                      </div>
                    </div>
                    <div class="repo-actions">
                      <button @click="changeRepo" class="change-repo-btn">
                        <i class="fas fa-exchange-alt"></i> Сменить
                      </button>
                      <a 
                        :href="linkedRepo.html_url" 
                        target="_blank" 
                        class="view-repo-btn"
                      >
                        <i class="fas fa-external-link-alt"></i> Открыть
                      </a>
                      <button @click="refreshCommits" class="refresh-btn">
                        <i class="fas fa-sync-alt"></i> Обновить
                      </button>
                    </div>
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
                            <i class="fas fa-external-link-alt"></i>
                          </a>
                        </div>
                        <div class="commit-message">{{ commit.message }}</div>
                        <div class="commit-date">{{ commit.author.date }}</div>
                      </div>
                    </div>
                    <div v-else class="empty-commits">
                      <i class="fas fa-code-branch empty-icon"></i>
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
                      <i class="fas fa-book repo-icon"></i>
                      <div class="repo-name-container">
                        <span class="repo-owner">{{ linkedRepo.full_name.split('/')[0] }}</span>
                        <span class="repo-name-divider">/</span>
                        <span class="repo-name">{{ linkedRepo.name }}</span>
                      </div>
                    </div>
                    <div class="repo-actions">
                      <button @click="changeRepo" class="change-repo-btn">
                        <i class="fas fa-exchange-alt"></i> Сменить
                      </button>
                      <a 
                        :href="linkedRepo.html_url" 
                        target="_blank" 
                        class="view-repo-btn"
                      >
                        <i class="fas fa-external-link-alt"></i> Открыть
                      </a>
                      <button @click="refreshPRs" class="refresh-btn">
                        <i class="fas fa-sync-alt"></i> Обновить
                      </button>
                    </div>
                  </div>
                  <div class="prs-list">
                    <div 
                      v-for="pr in pullRequests" 
                      :key="pr.id" 
                      class="pr-item"
                    >
                      <div class="pr-title-row">
                        <div class="pr-number">#{{ pr.number }}</div>
                        <div class="pr-title">{{ pr.title }}</div>
                        <div class="pr-status" :class="pr.state">{{ pr.state }}</div>
                      </div>
                      <div class="pr-info">
                        <div class="pr-author">
                          <img :src="pr.user.avatar_url || '/default-avatar.png'" class="pr-author-avatar">
                          <span>{{ pr.user.login }}</span>
                        </div>
                        <div class="pr-date">{{ pr.created_at ? formatDate(pr.created_at) : '' }}</div>
                        <a :href="pr.html_url" target="_blank" class="pr-link">
                          <i class="fas fa-external-link-alt"></i>
                        </a>
                      </div>
                    </div>
                    <div v-if="!pullRequests || pullRequests.length === 0" class="empty-prs">
                      <i class="fas fa-code-pull-request empty-icon"></i>
                      <p>Pull Requests не найдены</p>
                    </div>
                  </div>
                </div>

                <!-- Информация о репозитории (новая секция) -->
                <div v-if="selectedGitHubAction === 'repo-info'" class="action-content">
                  <div class="repo-header">
                    <div class="repo-info">
                      <i class="fas fa-book repo-icon"></i>
                      <div class="repo-name-container">
                        <span class="repo-owner">{{ linkedRepo.full_name.split('/')[0] }}</span>
                        <span class="repo-name-divider">/</span>
                        <span class="repo-name">{{ linkedRepo.name }}</span>
                      </div>
                    </div>
                    <div class="repo-actions">
                      <button @click="changeRepo" class="change-repo-btn">
                        <i class="fas fa-exchange-alt"></i> Сменить
                      </button>
                      <a 
                        :href="linkedRepo.html_url" 
                        target="_blank" 
                        class="view-repo-btn"
                      >
                        <i class="fas fa-external-link-alt"></i> Открыть
                      </a>
                      <button @click="refreshRepoInfo" class="refresh-btn">
                        <i class="fas fa-sync-alt"></i> Обновить
                      </button>
                    </div>
                  </div>
                  <div class="repo-details">
                    <div class="repo-detail-grid">
                      <div class="repo-detail-item">
                        <div class="detail-label"><i class="fas fa-user"></i> Владелец:</div>
                        <div class="detail-value">{{ repoDetails.owner }}</div>
                      </div>
                      <div class="repo-detail-item">
                        <div class="detail-label"><i class="fas fa-calendar-alt"></i> Дата создания:</div>
                        <div class="detail-value">{{ repoDetails.created_at || 'Н/Д' }}</div>
                      </div>
                      <div class="repo-detail-item">
                        <div class="detail-label"><i class="fas fa-sync"></i> Последнее обновление:</div>
                        <div class="detail-value">{{ repoDetails.updated_at || 'Н/Д' }}</div>
                      </div>
                      <div class="repo-detail-item">
                        <div class="detail-label"><i class="fas fa-star"></i> Звёзд:</div>
                        <div class="detail-value">{{ repoDetails.stars || 0 }}</div>
                      </div>
                      <div class="repo-detail-item">
                        <div class="detail-label"><i class="fas fa-code-branch"></i> Форков:</div>
                        <div class="detail-value">{{ repoDetails.forks || 0 }}</div>
                      </div>
                      <div class="repo-detail-item">
                        <div class="detail-label"><i class="fas fa-code"></i> Язык:</div>
                        <div class="detail-value">{{ repoDetails.language || 'Не указан' }}</div>
                      </div>
                    </div>
                    <div class="repo-url-item">
                      <div class="detail-label"><i class="fas fa-link"></i> URL:</div>
                      <a :href="repoDetails.html_url" target="_blank" class="repo-link">
                        {{ repoDetails.html_url }} <i class="fas fa-external-link-alt"></i>
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Если ничего не выбрано -->
              <div v-if="!selectedGitHubAction" class="github-empty-state">
                <div class="github-empty-icon">
                  <i class="fas fa-code-branch"></i>
                </div>
                <p class="github-empty-text">Выберите действие для работы с GitHub интеграцией</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Кнопки управления -->
      <div class="actions">
        <button @click="saveTask" class="save-button">Сохранить</button>
        <button @click="generateTaskReport" class="report-button">
          <i class="fas fa-chart-bar"></i> Отчёт по задаче
        </button>
        <button @click="closeModal" class="close-button">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import GitHubService from '@/services/GitHubService';
import DiscussionChat from '@/components/DiscussionChat.vue';
import * as XLSX from 'xlsx';
import MarkdownIt from 'markdown-it';

export default {
  name: 'TaskModal',
  components: { DiscussionChat },
  props: {
    task: { type: Object, required: true },
    board: { type: Object, required: true },
    currentUser: { type: Object, required: true },
  },
  data() {
    return {
      // Табы
      activeTab: 'general',
      tabs: [
        { id: 'general', icon: '/icons/info-icon.png' },
        { id: 'members', icon: '/icons/members-icon.png' },
        { id: 'discussion', icon: '/icons/discussion-icon.png' },
        { id: 'history', icon: '/icons/history-icon.png' },
        { id: 'github', icon: '/icons/github-icon.png' },
      ],

      // Локальная копия задачи
      localTask: {
        id: this.task && this.task.id || null,
        name: this.task && this.task.name || '',
        description: this.task && this.task.description || '',
        subtasks: Array.isArray(this.task && this.task.subtasks) ? [...this.task.subtasks] : [],
        files: Array.isArray(this.task && this.task.attachments) ? [...this.task.attachments] : [],
        members: Array.isArray(this.task && this.task.members) ? [...this.task.members] : [],
        priority: this.task && this.task.priority || 'medium',
        due_date: this.task.due_date ? this.task.due_date.split('T')[0] : null,
        column: this.task && this.task.column || null,
      },

      // Поля формы / стейты
      newSubtaskName: '',
      uploadedFiles: [],
      deletedFileIds: [],
      newMemberId: null,
      openDropdown: false,
      isEditingTitle: false,
      oldTitle: '',
      isEditingDescription: false,
      oldDescription: '',

      isParticipant: false,
      _historyInitialized: false,
      _completedMap: {},

      // Markdown-it
      md: new MarkdownIt({ html: true, linkify: true, typographer: true }),

      // GitHub
      selectedGitHubAction: '',
      githubSearchQuery: '',
      searchResults: [],
      linkedRepo: null,
      commits: [],
      pullRequests: [],
      recentRepos: [],
      repoDetails: {},
      isSearching: false,
    };
  },
  computed: {
    hasSubtasks() {
      return Array.isArray(this.localTask.subtasks) && this.localTask.subtasks.length > 0;
    },
    progress() {
      if (!this.hasSubtasks) return 0;
      const done = this.localTask.subtasks.filter(s => s && s.completed).length;
      return Math.round((done / this.localTask.subtasks.length) * 100);
    },
    renderedDescription() {
      const txt = (this.localTask.description || '').trim();
      return this.md.render(txt || '_Нет описания_');
    },
    historyLog() {
      return this.$store.getters['tasks/getHistory'](this.localTask.id) || [];
    },
    availableMembers() {
      // Используем id участников задачи (TaskMemberSerializer даёт поле id = user.id)
      const usedIds = (this.localTask.members || []).map(m => m.id);
      const all = (this.board && this.board.members) || [];
      return all.filter(bm =>
        bm.user_id != null &&
        bm.user_id !== this.currentUser.id &&
        !usedIds.includes(bm.user_id)
      );
    },
    availableMembersMap() {
      return Object.fromEntries(
        this.availableMembers.map(u => [u.user_id, u])
      );
    },
    isOwner() {
      return (
        this.currentUser &&
        this.board &&
        this.board.owner &&
        this.board.owner.email === this.currentUser.email
      );
    },
    minDueDate() {
      return this.localTask.created_at
        ? this.localTask.created_at.slice(0,10)
        : new Date().toISOString().slice(0,10);
    },
  },
  watch: {
    task: {

      immediate: true,
      deep: true,
      handler(newTask) {
        if (!newTask) return;
        // Обновляем локальную копию
        this.localTask = {
          id: newTask.id,
          name: newTask.name || '',
          description: newTask.description || '',
          subtasks: Array.isArray(newTask.subtasks) ? [...newTask.subtasks] : [],
          files: Array.isArray(newTask.attachments) ? [...newTask.attachments] : [],
          members: Array.isArray(newTask.members) ? [...newTask.members] : [],
          priority: newTask.priority || 'medium',
          due_date: newTask.due_date || null,
          column: newTask.column,
        };
        // Инициализация истории
        const serverHistory = Array.isArray(newTask.history) ? newTask.history : null;
        const existing = this.$store.getters['tasks/getHistory'](newTask.id) || [];
        if (serverHistory) {
          this.$store.commit('tasks/INIT_HISTORY', { taskId: newTask.id, events: serverHistory });
        } else if (!existing.length) {
          this.$store.commit('tasks/INIT_HISTORY', {
            taskId: newTask.id,
            events: [{
              user: this.currentUser.email,
              action: `создал задачу «${newTask.name}»`,
              ts: Date.now()
            }]
          });
        }
      }
    },
    selectedGitHubAction(action) {
      if (action === 'search' && this.githubSearchQuery) this.searchGitHubRepos();
      if (action === 'track-commits' && this.linkedRepo) this.refreshCommits();
      if (action === 'view-prs' && this.linkedRepo) this.refreshPRs();
      if (action === 'repo-info' && this.linkedRepo) this.refreshRepoInfo();
    },
  },
  methods: {
    // ——— TITLE ———
    startEditingTitle() {
      this.oldTitle = this.localTask.name || '';
      this.isEditingTitle = true;
      this.$nextTick(() => this.$refs.titleInput && this.$refs.titleInput.focus());
    },
    async stopEditingTitle() {
      if (this.oldTitle !== this.localTask.name) {
        const event = {
          user: this.currentUser.email,
          action: `изменил название задачи на «${this.localTask.name}»`,
          ts: Date.now()
        };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      }
      this.isEditingTitle = false;
    },

    // ——— DESCRIPTION ———
    startEditingDescription() {
      this.oldDescription = this.localTask.description;
      this.isEditingDescription = true;
      this.$nextTick(() => this.$refs.descriptionTextarea && this.$refs.descriptionTextarea.focus());
    },
    async stopEditingDescription() {
      if (this.oldDescription !== this.localTask.description) {
        const event = {
          user: this.currentUser.email,
          action: `изменил описание задачи`,
          ts: Date.now()
        };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      }
      this.isEditingDescription = false;
    },

    // ——— SUBTASKS ———
    async addSubtaskWithName() {
      const name = (this.newSubtaskName || '').trim();
      if (!name) return;
      this.localTask.subtasks = this.localTask.subtasks || [];
      this.localTask.subtasks.push({ id: null, name, completed: false, editing: false });
      const event = { user: this.currentUser.email, action: `добавил подзадачу «${name}»`, ts: Date.now() };
      this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
      await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      this.newSubtaskName = '';
      this.$nextTick(() => {
        this.adjustSubtasksHeight();
        this.scrollToLastSubtask();
      });
    },
    scrollToLastSubtask() {
      const el = this.$el.querySelector('.subtasks');
      if (el) el.scrollTop = el.scrollHeight;
    },
    adjustSubtasksHeight() {
      const el = this.$el.querySelector('.subtasks');
      if (!el) return;
      el.style.height = this.hasSubtasks ? 'auto' : '160px';
    },
    startEditingSubtask(i) {
      if (!(this.localTask.subtasks && this.localTask.subtasks[i])) return;
      this.oldSubtaskName = this.localTask.subtasks[i].name;
      this.localTask.subtasks[i].editing = true;
      this.$nextTick(() => this.$refs.subtaskInputs && this.$refs.subtaskInputs[i] && this.$refs.subtaskInputs[i].focus());
    },
    async stopEditingSubtask(i) {
      const sub = this.localTask.subtasks && this.localTask.subtasks[i];
      if (!sub) return;
      sub.editing = false;
      if (sub.name !== this.oldSubtaskName) {
        const event = { user: this.currentUser.email, action: `изменил название подзадачи на «${sub.name}»`, ts: Date.now() };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      }
    },
    async deleteSubtask(i) {
      const sub = this.localTask.subtasks && this.localTask.subtasks[i];
      if (!sub) return;
      this.localTask.subtasks.splice(i, 1);
      const event = { user: this.currentUser.email, action: `удалил подзадачу «${sub.name}»`, ts: Date.now() };
      this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
      await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
    },
    async updateProgress(i) {
      const s = this.localTask.subtasks && this.localTask.subtasks[i];
      if (!s) return;
      const prev = this._completedMap[i];
      if (prev !== undefined && prev !== s.completed) {
        const action = s.completed
          ? `отметил подзадачу «${s.name}» выполненной`
          : `снял отметку с подзадачи «${s.name}»`;
        const event = { user: this.currentUser.email, action, ts: Date.now() };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      }
      this._completedMap[i] = s.completed;
    },

    // ——— FILES ———
    async handleFileUpload(e) {
      const files = Array.from((e && e.target && e.target.files) || []);
      for (const file of files) {
        const reader = new FileReader();
        reader.onload = () => {
          this.localTask.files = this.localTask.files || [];
          this.localTask.files.push({ id: null, name: file.name, type: file.type, url: reader.result, isNew: true });
        };
        reader.readAsDataURL(file);
        const event = { user: this.currentUser.email, action: `прикрепил файл «${file.name}»`, ts: Date.now() };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      }
      this.uploadedFiles.push(...files);
      if (this.$refs.fileInput) this.$refs.fileInput.value = '';
    },
    async removeFile(i) {
      const f = this.localTask.files && this.localTask.files[i];
      if (!f) return;
      if (f.id) this.deletedFileIds.push(f.id);
      this.localTask.files.splice(i, 1);
      const event = { user: this.currentUser.email, action: `удалил файл «${f.name}»`, ts: Date.now() };
      this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
      await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
    },
    downloadFile(file) {
      if (!(file && file.url)) return;
      const link = document.createElement('a');
      link.href = file.url;
      link.download = file.name || '';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    // ——— MEMBERS ———
    selectMember(id) {
      this.newMemberId = id;
      this.openDropdown = false;
    },
    async assignTaskMember() {
      if (!this.newMemberId) return;
      await axios.post(`/api/tasks/${this.localTask.id}/members/`, { user_id: this.newMemberId }).catch(() => {});
      const u = this.availableMembersMap[this.newMemberId];
      if (u) this.localTask.members.push(u);
      const event = { user: u && u.email || '', action: `был назначен участником задачи`, ts: Date.now() };
      this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
      await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      await this.fetchTaskData();
    },
    async removeTaskMember(m) {
      await axios.delete(`/api/tasks/${this.localTask.id}/members/${m && m.id}/`).catch(() => {});
      const event = { user: m && m.email || '', action: `был исключен из участников задачи`, ts: Date.now() };
      this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
      await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      await this.fetchTaskData();
    },
    async checkParticipation() {
      if (!this.localTask.id) {
        this.isParticipant = false;
        return;
      }
      try {
        const response = await axios.get(`/api/tasks/${this.localTask.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        // Проверяем, есть ли текущий пользователь в списке участников
        this.isParticipant = response.data.members.some(m => m.email === this.$store.state.user.email);
      } catch (error) {
        console.error('Ошибка проверки участия:', error);
        this.isParticipant = false;
      }
    },
    async toggleParticipation() {
      if (!this.localTask.id) return;
      if (this.isParticipant) {
        await axios.delete(`/api/tasks/${this.localTask.id}/members/${this.currentUser.id}/`).catch(() => {});
        this.localTask.members = this.localTask.members.filter(m => m.id !== this.currentUser.id);
        const event = { user: this.currentUser.email, action: `отказался от участия`, ts: Date.now() };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      } else {
        await axios.post(`/api/tasks/${this.localTask.id}/members/`, {}).catch(() => {});
        this.localTask.members.push({ id: this.currentUser.id, email: this.currentUser.email, avatar: this.currentUser.avatar });
        const event = { user: this.currentUser.email, action: `присоединился к участникам задачи`, ts: Date.now() };
        this.$store.commit('tasks/ADD_EVENT', { taskId: this.localTask.id, event });
        await axios.post(`/api/tasks/${this.localTask.id}/history/`, event).catch(() => {});
      }
      this.isParticipant = !this.isParticipant;
    },

    // ——— LOAD / SAVE ———
    async fetchTaskData() {
      if (!this.localTask.id) return;

      // 1. Получаем данные
      const { data } = await axios
        .get(`/api/tasks/${this.localTask.id}/`)
        .catch(() => ({ data: {} }));

      // 2. Обновляем локальную задачу, нормализуя файлы и подтягивая due_date и created_at
      Object.assign(this.localTask, {
        name: data.name || '',
        description: data.description || '',
        subtasks: Array.isArray(data.subtasks) ? data.subtasks : [],
        priority: data.priority || this.localTask.priority,
        created_at: data.created_at || this.localTask.created_at,   // для minDueDate
        due_date: data.due_date || null,                           // новое поле срок
        members: Array.isArray(data.members) ? data.members : [],
        files: (Array.isArray(data.attachments) ? data.attachments : [])
          .map(a => ({
            ...a,
            // гарантируем, что url у нас всегда есть
            url: a.url || a.file
          }))
      });

      // 3. Инициализация completedMap и истории (без изменений)
      if (!this._historyInitialized) {
        (this.localTask.subtasks || []).forEach((s, idx) => {
          this._completedMap[idx] = !!s.completed;
        });
        this._historyInitialized = true;

        const existing = this.$store.getters['tasks/getHistory'](this.localTask.id) || [];
        if (!existing.length) {
          this.$store.commit('tasks/INIT_HISTORY', {
            taskId: this.localTask.id,
            events: [{
              user: this.currentUser.email,
              action: `создал задачу «${data.name}»`,
              ts: Date.now()
            }]
          });
        }
      }

      // 4. Проверяем участие
      const me = await axios.get('/api/users/me/').catch(() => ({ data: {} }));
      this.isParticipant = (this.localTask.members || [])
        .some(m => m && m.id === me.data.id);
    },
    async saveTask() {
      const form = new FormData();
      form.append('name', this.localTask.name || '');
      form.append('description', this.localTask.description || '');
      form.append('priority', this.localTask.priority || '');
      form.append('due_date', this.localTask.due_date || '');
      form.append('column', this.localTask.column || '');
      form.append('subtasks', JSON.stringify(
        (this.localTask.subtasks || []).map(s => ({
          id: s.id,
          name: s.name,
          completed: !!s.completed
        }))
      ));
      (this.uploadedFiles || []).forEach(f => form.append('attachments', f));
      if ((this.deletedFileIds || []).length) {
        form.append('deleted_files', JSON.stringify(this.deletedFileIds));
      }
      await axios.patch(`/api/tasks/${this.localTask.id}/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).catch(() => {});
      await this.fetchTaskData();
      this.$emit('saveTask', this.localTask);
      this.$emit('close');
    },

    // ——— GITHUB ———
    async searchGitHubRepos() {
      if (!(this.githubSearchQuery || '').trim()) { this.searchResults = []; return; }
      this.isSearching = true;
      this.searchResults = await GitHubService.searchRepositories(this.githubSearchQuery).catch(() => []);
      this.isSearching = false;
    },
    async selectRepo(repo) {
      this.linkedRepo = repo;
      this.searchResults = [];
      this.githubSearchQuery = '';
      await this.refreshCommits();
    },
    async refreshCommits() {
      if(!(this.linkedRepo && this.linkedRepo.full_name)) return;
      this.commits = [];
      this.commits = await GitHubService.getCommits(this.linkedRepo.full_name).catch(() => []);
    },
    async refreshPRs() {
      if(!(this.linkedRepo && this.linkedRepo.full_name)) return;
      this.pullRequests = await GitHubService.getPullRequests(this.linkedRepo.full_name).catch(() => []);
    },
    async linkRepository() {
      if (!this.repoUrl) { alert('Введите URL репозитория'); return; }
      try {
        const { fullName } = GitHubService.parseRepositoryUrl(this.repoUrl);
        const repoData = await GitHubService.getRepository(fullName);
        await GitHubService.linkRepository(repoData.full_name, this.localTask.id);
        this.linkedRepo = repoData;
        this.repoUrl = '';
        await this.fetchRecentRepos();
      } catch (e) {
        console.error(e);
        alert('Не удалось привязать репозиторий.');
      }
    },
    async fetchRecentRepos() {
      this.recentRepos = await GitHubService.getRecentRepositories().catch(() => []);
    },
    async refreshRepoInfo() {
      if(!(this.linkedRepo && this.linkedRepo.full_name)) return;
      this.repoDetails = await GitHubService.getRepositoryInfo(this.linkedRepo.full_name).catch(() => ({}));
    },

    // ——— REPORT ———
    async generateTaskReport() {
      try {
        const response = await axios.get(`/api/reports/`, {
          params: { report_type: 'tasks', task_id: this.localTask.id },
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        const wb = XLSX.utils.book_new();
        const info = [ {
          'Название': response.data.name,
          'Описание': response.data.description,
          'Приоритет': response.data.priority,
          'Участники': (response.data.members || []).join(', '),
          'Создано': new Date(response.data.created_at).toLocaleDateString(),
          'Обновлено': new Date(response.data.updated_at).toLocaleDateString(),
          'Срок выполнения': new Date(response.data.due_date).toLocaleDateString()
        } ];
        XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(info), 'Задача');
        if (this.hasSubtasks) {
          const st = this.localTask.subtasks.map(s => ({
            Название: s.name,
            Статус: s.completed ? 'Выполнено' : 'Не выполнено'
          }));
          XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(st), 'Подзадачи');
        }
        XLSX.writeFile(wb, `task_report_${this.localTask.id}_${Date.now()}.xlsx`);
      } catch (e) {
        console.error(e);
        alert('Не удалось сформировать отчёт');
      }
    },

    // ——— UI helpers ———
    closeModal() {
      this.$emit('close');
    },
    isImage(type) {
      return typeof type === 'string' && type.startsWith('image/');
    },
    renderMarkdown(text) {
      return this.md.render(text || '');
    },
    formatTs(ts) {
      const d = new Date(ts);
      return d.toLocaleString('ru-RU', { 
        day:'2-digit', month:'2-digit', year:'numeric', 
        hour:'2-digit', minute:'2-digit' 
      });
    },
    displayName(obj) {
      // obj может быть либо { first_name, last_name, email }, либо { email: 'user@...' }
      const name = [obj.first_name, obj.last_name].filter(Boolean).join(' ');
      return name || obj.email || '';
    },
    formatForInput(dateString) {
      if (!dateString) return null;
      const d = new Date(dateString);
      const pad = n => String(n).padStart(2, '0');
      return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
    },
  },
  mounted() {
    if (this.localTask && this.localTask.id) {
      this.fetchTaskData();
      this.checkParticipation && this.checkParticipation();
    }
    this.$nextTick(() => this.adjustSubtasksHeight());
  }
};
</script>

<style scoped>
.modal {
  overflow: visible !important;
  backdrop-filter: none;
}

.modal-content {
  position: relative;
  padding-left: 60px;
  overflow: visible !important; /* Разрешаем выход за границы */
  background-clip: padding-box; /* Сохраняем обрезку фона */
}

.sticky-tabs {
  position: absolute;
  left: -50px; /* Увеличиваем выступ за край */
  top: 40%;
  transform: translateY(-40%);
  z-index: 1003; /* Повышаем над всеми элементами */
  filter: drop-shadow(-5px 5px 10px rgba(0,0,0,0.1)); /* Добавляем тень */
  pointer-events: auto;
}

.tab {
  background: #fff9e6;
  padding: 14px 24px;
  border-radius: 8px 0 0 8px;
  transform: rotate(-4deg);
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  position: relative;
  font-family: 'Caveat', cursive;
  font-size: 20px;
  color: #6d4c41;
  margin-left: -35px;
  clip-path: inset(-20px -20px -20px 0); /* Разрешаем отображение за пределами */
}

.tab:nth-child(2) { transform: rotate(-2deg); z-index: 1; margin-left: -30px; }
.tab:nth-child(3) { transform: rotate(0deg); z-index: 2; margin-left: -25px; }
.tab:nth-child(4) { transform: rotate(2deg); z-index: 3; margin-left: -20px; }
.tab:nth-child(5) { transform: rotate(1deg); z-index: 4; margin-left: -20px; }

.tab::after {
  transform: none !important;
  margin-left: 0 !important;
  position: relative;
  left: 0;
  border-width: 12px 12px 12px 0;
  border-style: solid;
  border-color: transparent #fff9e6 transparent transparent;
}

.tab-icon {
  width: 28px;
  height: 28px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.tab.color-0 { background: #ff6b6b; } /* Красный */
.tab.color-1 { background: #ffa500; } /* Оранжевый */
.tab.color-2 { background: #4CAF50; } /* Зеленый */
.tab.color-3 { background: #5b9cff; } /* Голубой */
.tab.color-4 { background: #d8b4fe; } /* Фиолетовый */

.tab.active {
  transform: rotate(-1deg) !important;
  filter: brightness(85%) !important;
  z-index: 5;
}

.tab:hover {
  transform: rotate(-3deg) !important;

}

.modal-body-with-tabs {
  overflow-y: auto;
  overflow-x: hidden !important;
  max-height: calc(100vh - 160px);
  padding: 10px;
}

.tab-content {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  min-height: 400px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tab-pane {
  animation: fadeIn 0.3s ease;
  overflow: auto !important;
  flex: 1;
  overflow: auto;
}

.modal-body-with-tabs {
  overflow-y: auto !important;  /* возвращаем вертикальную прокрутку */
  overflow-x: hidden;            /* по горизонтали скрываем лишнее */
}
.tab-content,
.tab-pane {
  overflow: visible;             /* если внутри этих блоков прокрутка не нужна */
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Убираем горизонтальный scroll и растягиваем на всю ширину */
.description-input,
.description-preview {
  width: 100%;
  box-sizing: border-box;
  white-space: pre-wrap; /* чтобы Markdown-превью не склеивалось */
}

/* Стилизуем превью */
.description-preview {
  padding: 10px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  background: #fafafa;
  min-height: 80px;
  overflow-y: auto;
}

/* Иконка редактирования */
.description-label {
  display: flex;
  align-items: center;
  gap: 6px;
}
.edit-icon {
  width: 18px;
  height: 18px;
  cursor: pointer;
  filter: grayscale(1) brightness(0.5);
  transition: filter .2s;
}
.edit-icon:hover {
  filter: none;
}

.no-description {
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #64748b; /* можно настроить цвет под общий стиль */
  font-style: italic; /* опционально, чтобы сохранить курсив из Markdown */
}

/* Адаптация остальных стилей */
.subtasks {
  max-height: 40vh;
}

.github-content {
  max-height: 50vh;
}

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
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1001;
  padding: 20px;
  box-sizing: border-box;
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
  padding: 0 0 0 0; /* Убираем все отступы контента */
  border-radius: 12px;
  width: 550px; /* Немного уменьшаем ширину */
  max-width: 90%; 
  max-height: 90vh;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 1005;
  display: flex;
  flex-direction: column;
  position: relative;
  animation: slideIn 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.4);
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.modal-content::before {
  content: "";
  position: absolute;
  left: 0;
  top: 20.5%;
  width: 9px;                   /* = padding-left, подгоните под ваш отступ */
  height: 50%;
  background: #f0f0f0; /* совпадает с фоном .modal-content */
  pointer-events: none;          /* не блокирует клики по табам */
  z-index: 1004;                 /* между фоном и табами */
}

.task-header {
  margin-bottom: 0;
  position: sticky;
  top: 0;
  background: rgba(91, 156, 255, 0.1);
  padding: 20px 25px;
  z-index: 10;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 12px 12px 0 0;
}

.task-title {
  font-size: 1.8em;
  font-weight: bold;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #2c3e50;
  letter-spacing: 0.3px;
}

.task-title-input {
  font-size: 1.8em;
  font-weight: bold;
  width: 100%;
  padding: 8px;
  border: 2px solid #5b9cff;
  border-radius: 8px;
  margin-bottom: 0;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

/* Добавляем контейнер для основного содержимого с отступами */
.modal-body {
  padding: 20px 25px;
}

/* Обернем все внутреннее содержимое в контейнер */
.form-group {
  margin-bottom: 15px; /* Уменьшаем отступы */
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.form-group label {
  display: block;
  margin-bottom: 8px; /* Уменьшаем отступы */
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 15px;
  letter-spacing: 0.2px;
}

.due-date-group {
  margin-top: 10px;
}
.due-date-input {
  width: 100%;      /* чтобы не выступал вправо */
  box-sizing: border-box;
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.description-input {
  width: 100%;
  min-height: 80px; /* Уменьшаем высоту */
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 0;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
  resize: vertical;
}

.progress-container {
  margin: 15px 0;
  padding: 8px 0;
}

.progress-bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
}

.progress {
  height: 100%;
  background: linear-gradient(to right, #5b9cff, #82c0ff);
  transition: width 0.4s cubic-bezier(0.25, 1, 0.5, 1);
  border-radius: 20px;
  box-shadow: 0 1px 2px rgba(91, 156, 255, 0.3);
}

.progress-text {
  text-align: right;
  font-size: 0.85em;
  color: #64748b;
  margin-top: 6px;
  letter-spacing: 0.2px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-weight: 500;
}

.subtask-add-form {
  display: flex;
  gap: 10px;
  margin: 10px 0;
  width: 100%;
}

.subtask-name-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 14px;
}

.add-subtask-button {
  width: auto;
  flex: 0 0 auto;
  padding: 10px 15px;
  background: #f0f0f0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #4a5568;
}

.subtasks {
  margin: 10px 0;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  min-height: 120px; /* Уменьшаем минимальную высоту */
  max-height: 250px; /* Ограничиваем максимальную высоту */
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.subtask {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
  padding: 8px 12px;
  min-height: 32px;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.subtask:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.subtask input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #5b9cff;
}

.subtask-title {
  flex: 1;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  letter-spacing: 0.2px;
}

.subtask-title:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.subtask input[type="checkbox"]:checked + .subtask-title {
  text-decoration: line-through;
  color: #94a3b8;
  font-weight: 400;
}

.delete-subtask-button {
  background: none;
  border: none;
  color: #cbd5e1;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: 0.5;
}

.subtask:hover .delete-subtask-button {
  opacity: 1;
}

.delete-subtask-button:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  transform: rotate(90deg);
}

.subtask-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #5b9cff;
  border-radius: 6px;
  font-size: 14px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  outline: none;
  box-shadow: 0 0 0 2px rgba(91, 156, 255, 0.1);
}

.file-section, .participants-section, .github-section {
  margin: 15px 0;
  padding: 15px 0;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.file-list {
  max-height: 150px; /* Уменьшаем максимальную высоту */
  overflow-y: auto;
  margin-bottom: 15px;
}

.file-item {
  padding: 8px;
  margin-bottom: 8px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(250, 250, 250, 0.95);
  padding: 15px 25px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin: 0;
  border-radius: 0 0 12px 12px;
  z-index: 100;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 -5px 10px rgba(0, 0, 0, 0.02);
}

.save-button {
  background: #5b9cff;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
  letter-spacing: 0.3px;
}

.save-button:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.close-button {
  background: #f0f0f0;
  color: #4a5568;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
}

.close-button:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

.file-section label {
  display: block;
  margin-bottom: 15px;
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 16px;
  letter-spacing: 0.2px;
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
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  color: #2c3e50;
}

.delete-file {
  background: none;
  border: none;
  color: #bdc3c7;
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.delete-file:hover {
  background: rgba(231, 76, 60, 0.1);
  color: #e74c3c;
  transform: rotate(90deg);
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
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  display: inline-block;
  transition: all 0.3s ease;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 15px;
  font-weight: 500;
  color: #4a5568;
}

.upload-button:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.07);
}

.file-icon-img {
  width: 24px; /* Размер иконки */
  height: 24px;
  object-fit: contain; /* Сохраняет пропорции */
}

.participants-section label {
  display: block;
  margin-bottom: 15px;
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 16px;
  letter-spacing: 0.2px;
}

.participants-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 15px 0;
}

.participant {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

.participant:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.participant:hover .avatar {
  transform: scale(1.05);
}

.participation-btn {
  padding: 12px 20px;
  background: #5b9cff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
  letter-spacing: 0.3px;
}

.participation-btn:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

.participation-btn.joined {
  background: #e74c3c;
}

.participation-btn.joined:hover {
  background: #c0392b;
  box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
}

.participation-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  box-shadow: none;
}

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

.github-section label {
  display: block;
  margin-bottom: 15px;
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-size: 16px;
  letter-spacing: 0.2px;
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
  margin: auto;
  font-size: 16px;
  letter-spacing: 0.2px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

/* Модификация скроллбаров для соответствия общему стилю */
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

.input-error {
  color: #e74c3c;
  font-size: 14px;
  margin-top: 5px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}

.task-title-input.error {
  border-color: #e74c3c;
}

/* Стилизация интеграции с GitHub */
.github-section {
  margin: 0;
  padding: 0;
}

.github-header {
  margin-bottom: 20px;
}

.github-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.github-logo h3 {
  margin: 0;
  font-size: 18px;
  color: #24292e;
}

.github-logo-img {
  width: 32px;
  height: 32px;
}

.github-description {
  color: #586069;
  font-size: 14px;
  margin: 0 0 15px 0;
  line-height: 1.5;
}

.github-action-wrapper {
  margin-bottom: 20px;
}

.github-action-wrapper label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #24292e;
}

.github-action-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  color: #24292e;
  appearance: none;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="%23586069" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>');
  background-repeat: no-repeat;
  background-position: right 12px center;
  transition: border-color 0.2s ease;
}

.github-action-select:focus {
  border-color: #2188ff;
  outline: none;
  box-shadow: 0 0 0 3px rgba(33, 136, 255, 0.2);
}

.github-content-wrapper {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 16px;
  margin-top: 15px;
}

.repo-selection-container {
  background: white;
  border-radius: 6px;
  overflow: hidden;
}

.repo-selection-title {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #24292e;
  font-weight: 600;
}

.repo-tabs {
  display: flex;
  background: #f6f8fa;
  border-bottom: 1px solid #e1e4e8;
  margin-bottom: 15px;
}

.tab-btn {
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  color: #586069;
  transition: all 0.2s ease;
  flex: 1;
  text-align: center;
}

.tab-btn.active {
  color: #2188ff;
  border-bottom-color: #2188ff;
  background: white;
  font-weight: 600;
}

.tab-btn:hover:not(.active) {
  color: #24292e;
  background: rgba(27, 31, 35, 0.05);
}

.repo-tab-content {
  padding: 0 15px 15px;
}

.search-input-wrapper, .link-input-wrapper {
  position: relative;
  margin-bottom: 15px;
}

.search-icon, .link-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6a737d;
}

.github-search-input, .repo-url-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 14px;
  color: #24292e;
  background: white;
  transition: all 0.2s ease;
}

.github-search-input:focus, .repo-url-input:focus {
  border-color: #2188ff;
  outline: none;
  box-shadow: 0 0 0 3px rgba(33, 136, 255, 0.2);
}

.search-loader {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.loader {
  width: 24px;
  height: 24px;
  border: 3px solid #e1e4e8;
  border-radius: 50%;
  border-top-color: #2188ff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.search-results, .recent-repos {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
}

.repo-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e1e4e8;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.repo-item:last-child {
  border-bottom: none;
}

.repo-item:hover {
  background-color: #f6f8fa;
}

.repo-item-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.repo-icon {
  color: #586069;
  width: 16px;
}

.repo-name {
  font-weight: 600;
  color: #0366d6;
  font-size: 14px;
}

.repo-description {
  color: #586069;
  font-size: 13px;
  line-height: 1.4;
}

.no-results, .no-repos-message {
  padding: 30px 20px;
  text-align: center;
  color: #586069;
}

.no-results i, .no-repos-message i {
  font-size: 24px;
  margin-bottom: 10px;
  color: #d1d5da;
  display: block;
}

.link-help-text {
  font-size: 13px;
  color: #586069;
  margin: 10px 0 15px;
}

.link-repo-btn {
  width: 100%;
  padding: 10px 16px;
  background: #2ea44f;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.link-repo-btn:hover:not(:disabled) {
  background: #2c974b;
}

.link-repo-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.repo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.repo-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.repo-name-container {
  display: flex;
  align-items: center;
}

.repo-owner {
  color: #586069;
  font-size: 14px;
}

.repo-name-divider {
  color: #586069;
  margin: 0 4px;
}

.repo-actions {
  display: flex;
  gap: 10px;
}

.change-repo-btn, .refresh-btn {
  padding: 6px 12px;
  background: #f6f8fa;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 13px;
  color: #24292e;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.change-repo-btn:hover, .refresh-btn:hover {
  background: #e1e4e8;
}

.view-repo-btn {
  padding: 6px 12px;
  background: #0366d6;
  border: 1px solid #0366d6;
  border-radius: 6px;
  font-size: 13px;
  color: white;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.view-repo-btn:hover {
  background: #0058c7;
}

.action-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.action-header h4 {
  margin: 0;
  font-size: 16px;
  color: #24292e;
}

.commits-list, .prs-list {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  overflow: hidden;
  max-height: 400px;
  overflow-y: auto;
}

.commit-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e1e4e8;
}

.commit-item:last-child {
  border-bottom: none;
}

.commit-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  margin-right: 8px;
}

.author-name {
  font-weight: 600;
  color: #24292e;
  font-size: 14px;
  margin-right: auto;
}

.commit-link {
  color: #0366d6;
  text-decoration: none;
  font-size: 14px;
}

.commit-message {
  color: #24292e;
  font-size: 14px;
  margin-bottom: 8px;
  word-break: break-word;
}

.commit-date {
  color: #586069;
  font-size: 12px;
}

.empty-commits, .empty-prs {
  padding: 40px 20px;
  text-align: center;
  color: #586069;
}

.empty-icon {
  font-size: 24px;
  margin-bottom: 10px;
  color: #d1d5da;
  display: block;
}

.repo-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 15px;
}

.repo-detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  color: #586069;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-value {
  color: #24292e;
  font-size: 14px;
  font-weight: 600;
}

.repo-url-item {
  padding-top: 15px;
  border-top: 1px solid #e1e4e8;
}

.repo-link {
  color: #0366d6;
  text-decoration: none;
  font-size: 14px;
  word-break: break-all;
}

.pr-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e1e4e8;
}

.pr-item:last-child {
  border-bottom: none;
}

.pr-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.pr-number {
  color: #586069;
  font-size: 14px;
  flex-shrink: 0;
}

.pr-title {
  font-weight: 600;
  color: #24292e;
  font-size: 14px;
  flex: 1;
  word-break: break-word;
}

.pr-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.pr-author {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #586069;
}

.pr-author-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.pr-date {
  font-size: 13px;
  color: #586069;
}

.pr-link {
  margin-left: auto;
  color: #0366d6;
  text-decoration: none;
  font-size: 13px;
}

.pr-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.pr-status.open {
  background: rgba(46, 164, 79, 0.15);
  color: #22863a;
}

.pr-status.closed {
  background: rgba(215, 58, 73, 0.15);
  color: #cb2431;
}

.github-empty-state {
  text-align: center;
  padding: 40px 0;
}

.github-empty-icon {
  font-size: 36px;
  color: #d1d5da;
  margin-bottom: 15px;
}

.github-empty-text {
  color: #586069;
  font-size: 16px;
}

/* Дополнительная анимация для hover на пунктах */
.repo-item, .pr-item, .commit-item {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.repo-item:hover, .pr-item:hover, .commit-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  z-index: 1;
  position: relative;
}

/* Error commit styling */
.error-commit {
  background-color: rgba(215, 58, 73, 0.05);
  border-left: 3px solid #cb2431;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-control {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

select.form-control {
  height: 36px;
}

.report-button {
  /* Применяем стиль, похожий на close-button */
  background: #f0f0f0;
  color: #4a5568;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  transition: all 0.3s ease;
  display: flex; /* Добавляем для выравнивания иконки */
  align-items: center; /* Выравниваем иконку по центру */
  gap: 8px; /* Добавляем отступ для иконки */
}

.report-button:hover {
  /* Стиль при наведении, как у close-button */
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

/* Контейнер для назначения участника */
.assign-participant {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

/* Селектор выбора нового участника */
.custom-dropdown {
  position: relative;
  width: 100%;
  font-family: 'Segoe UI', sans-serif;
}
.custom-dropdown .selected {
  padding: 10px 12px;
  border: 1px solid #d1d5da;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
  min-width: 180px;
}
.custom-dropdown .arrow {
  transition: transform .2s;
}
.custom-dropdown .arrow.open {
  transform: rotate(180deg);
}
.custom-dropdown .dropdown-list {
  padding-left: 0;
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5da;
  border-radius: 8px;
  padding: 4px 0;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  z-index: 10;
  list-style: none;
  margin: 0;
}

.custom-dropdown .dropdown-item {
  padding: 8px 12px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background .2s;
}
.custom-dropdown .dropdown-item:hover {
  background: rgba(91,156,255,0.1);
}
.custom-dropdown .item-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

/* Кнопка «Назначить участника» */
.assign-btn {
  padding: 10px 16px;
  background: #5b9cff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 4px 15px rgba(91,156,255,0.3);
}
.assign-btn:hover:not(:disabled) {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91,156,255,0.4);
}
.assign-btn:disabled {
  background: #ccc;
  box-shadow: none;
  cursor: not-allowed;
}

/* Кнопка удаления участника внутри .participant */
.remove-member-btn {
  background: none;
  border: none;
  color: #bdc3c7;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
  margin-left: 4px;
}
.remove-member-btn:hover {
  background: rgba(231,76,60,0.1);
  color: #e74c3c;
  transform: rotate(90deg);
}

</style>