<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { format } from 'date-fns'
import type { FormInst, FormRules } from 'naive-ui'
import { createGift, updateGift } from '../api/gift'
import type { Gift, GiftFormData } from '../types/gift'

const props = defineProps<{
  show: boolean
  gift: Gift | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const isEdit = computed(() => props.gift !== null)

const defaultForm = (): GiftFormData => ({
  item_name: '',
  description: '',
  gift_date: format(new Date(), 'yyyy-MM-dd'),
  recipient_nickname: '',
  is_taken: false,
})

const formModel = ref<GiftFormData>(defaultForm())

const rules: FormRules = {
  item_name: [{ required: true, message: '请输入物品名', trigger: ['blur', 'input'] }],
  gift_date: [{ required: true, message: '请选择赠送日期', trigger: ['blur', 'change'] }],
}

/** 弹窗标题 */
const modalTitle = computed(() => (isEdit.value ? '编辑赠送记录' : '新增赠送记录'))

/** 根据传入记录同步表单 */
watch(
  () => [props.show, props.gift] as const,
  ([visible, gift]) => {
    if (!visible) return
    if (gift) {
      formModel.value = {
        item_name: gift.item_name,
        description: gift.description,
        gift_date: gift.gift_date,
        recipient_nickname: gift.recipient_nickname,
        is_taken: gift.is_taken,
      }
    } else {
      formModel.value = defaultForm()
    }
  },
  { immediate: true },
)

/** 关闭弹窗 */
function handleClose(): void {
  emit('update:show', false)
}

/** 提交表单 */
async function handleSubmit(): Promise<void> {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (isEdit.value && props.gift) {
      await updateGift(props.gift.id, formModel.value)
    } else {
      await createGift(formModel.value)
    }
    emit('saved')
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
    style="width: 520px"
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
      <n-form-item label="物品名" path="item_name">
        <n-input v-model:value="formModel.item_name" placeholder="例如：儿童绘本一套" />
      </n-form-item>

      <n-form-item label="描述" path="description">
        <n-input
          v-model:value="formModel.description"
          type="textarea"
          placeholder="物品品相、数量等说明"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </n-form-item>

      <n-form-item label="赠送日期" path="gift_date">
        <n-date-picker
          v-model:formatted-value="formModel.gift_date"
          value-format="yyyy-MM-dd"
          type="date"
          style="width: 100%"
          clearable
        />
      </n-form-item>

      <n-form-item label="接收方昵称" path="recipient_nickname">
        <n-input
          v-model:value="formModel.recipient_nickname"
          placeholder="领取人社区昵称"
        />
      </n-form-item>

      <n-form-item label="是否已取走" path="is_taken">
        <n-switch v-model:value="formModel.is_taken">
          <template #checked>已取走</template>
          <template #unchecked>待取走</template>
        </n-switch>
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
