<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { format } from 'date-fns'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { createAnnouncement, updateAnnouncement } from '../api/announcement'
import type { Announcement, AnnouncementFormData } from '../types/announcement'

const props = defineProps<{
  show: boolean
  announcement: Announcement | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const isEdit = computed(() => props.announcement !== null)

const defaultForm = (): AnnouncementFormData => ({
  title: '',
  content: '',
  publisher_nickname: '',
  publish_time: format(new Date(), 'yyyy-MM-dd HH:mm:ss'),
  is_pinned: false,
})

const formModel = ref<AnnouncementFormData>(defaultForm())

const rules: FormRules = {
  title: [{ required: true, message: '请输入公告标题', trigger: ['blur', 'input'] }],
  content: [{ required: true, message: '请输入公告正文', trigger: ['blur', 'input'] }],
  publisher_nickname: [{ required: true, message: '请输入发布人昵称', trigger: ['blur', 'input'] }],
  publish_time: [{ required: true, message: '请选择发布时间', trigger: ['blur', 'change'] }],
}

const modalTitle = computed(() => (isEdit.value ? '编辑公告' : '发布公告'))

watch(
  () => props.show,
  (visible) => {
    if (!visible) return
    if (props.announcement) {
      formModel.value = {
        title: props.announcement.title,
        content: props.announcement.content,
        publisher_nickname: props.announcement.publisher_nickname,
        publish_time: props.announcement.publish_time,
        is_pinned: props.announcement.is_pinned,
      }
    } else {
      formModel.value = defaultForm()
    }
  },
  { immediate: true },
)

function handleClose(): void {
  emit('update:show', false)
}

async function handleSubmit(): Promise<void> {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    if (isEdit.value && props.announcement) {
      await updateAnnouncement(props.announcement.id, formModel.value)
    } else {
      await createAnnouncement(formModel.value)
    }
    emit('saved')
    message.success(isEdit.value ? '公告更新成功' : '公告发布成功')
  } catch (e: any) {
    const msg = e?.response?.data?.error || '提交失败，请稍后重试'
    message.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="modalTitle"
    style="width: 560px"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="left"
      label-width="100"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="公告标题" path="title">
        <n-input v-model:value="formModel.title" placeholder="请输入公告标题" maxlength="100" show-count />
      </n-form-item>

      <n-form-item label="公告正文" path="content">
        <n-input
          v-model:value="formModel.content"
          type="textarea"
          placeholder="请输入公告正文内容"
          :autosize="{ minRows: 5, maxRows: 10 }"
          maxlength="2000"
          show-count
        />
      </n-form-item>

      <n-form-item label="发布人昵称" path="publisher_nickname">
        <n-input v-model:value="formModel.publisher_nickname" placeholder="例如：物业管理员小王" maxlength="50" />
      </n-form-item>

      <n-form-item label="发布时间" path="publish_time">
        <n-date-picker
          v-model:formatted-value="formModel.publish_time"
          value-format="yyyy-MM-dd HH:mm:ss"
          type="datetime"
          style="width: 100%"
          clearable
        />
      </n-form-item>

      <n-form-item label="是否置顶" path="is_pinned">
        <n-switch v-model:value="formModel.is_pinned">
          <template #checked>已置顶</template>
          <template #unchecked>未置顶</template>
        </n-switch>
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="footer">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '发布' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
