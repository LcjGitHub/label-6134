<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { createCategory, updateCategory } from '../api/category'
import type { Category, CategoryFormData } from '../types/category'

const props = defineProps<{
  show: boolean
  category: Category | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const isEdit = computed(() => props.category !== null)

const defaultForm = (): CategoryFormData => ({
  name: '',
  sort_order: 0,
})

const formModel = ref<CategoryFormData>(defaultForm())

const rules: FormRules = {
  name: [{ required: true, message: '请输入类别名称', trigger: ['blur', 'input'] }],
  sort_order: [
    {
      type: 'number',
      required: true,
      message: '请输入排序序号',
      trigger: ['blur', 'input'],
    },
  ],
}

const modalTitle = computed(() => (isEdit.value ? '编辑类别' : '新增类别'))

watch(
  () => [props.show, props.category] as const,
  ([visible, category]) => {
    if (!visible) return
    if (category) {
      formModel.value = {
        name: category.name,
        sort_order: category.sort_order,
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
    if (isEdit.value && props.category) {
      await updateCategory(props.category.id, formModel.value)
      message.success('类别更新成功')
    } else {
      await createCategory(formModel.value)
      message.success('类别创建成功')
    }
    emit('saved')
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
    style="width: 460px"
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
      <n-form-item label="类别名称" path="name">
        <n-input v-model:value="formModel.name" placeholder="例如：图书文具" maxlength="32" />
      </n-form-item>

      <n-form-item label="排序序号" path="sort_order">
        <n-input-number
          v-model:value="formModel.sort_order"
          :min="0"
          :max="9999"
          placeholder="数值越小越靠前"
          style="width: 100%"
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="footer">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
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
