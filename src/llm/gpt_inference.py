import os, copy, time
from openai import OpenAI
from utils.llm_client import LLMClient
from src.tools.utils import open_json, save_json, cut_cottable_prompt, add_process_time
from global_values import *
if OPENAI_BASE_URL is not None:
    os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL

class GPTPOOL:
    def __init__(self, key_file=KEY_FILE, model="gpt-3.5-turbo-0301", temp=LLM_HYPER_PARAMS['temperature'], root_dir = './tmp/gpt', record_log=False, print_key=False):
        self.key_file = key_file
        self.model = model
        self.temp = temp
        self.client = None
        self.local_client = None
        self.root_dir = root_dir
        self.record_log = record_log
        if os.path.exists(os.path.join(root_dir, 'log.json')):
            self.log = open_json(os.path.join(root_dir, 'log.json'))
        else:
            self.log = {}
        self.print_key = print_key

    def get_key(self):
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            self.cur_key = env_key
            return env_key

        if not os.path.exists(self.key_file):
            raise FileNotFoundError(f"Missing key file: {self.key_file}")

        with open(self.key_file, 'r') as f:
            keys = [x.strip() for x in f.readlines() if x.strip()]

        if not keys:
            raise ValueError(f"No API keys found in {self.key_file}")

        cur_key = copy.deepcopy(keys[0])
        keys = keys[1:] + [cur_key]

        with open(self.key_file, 'w') as f:
            f.write('\n'.join(keys))

        self.cur_key = cur_key
        return cur_key
    
    def _encode(self, ask, dim):
        key = self.get_key()
        if self.print_key:
            print(f'cur_key: {key}')
        os.environ["OPENAI_API_KEY"] = key
        if self.client is None:
            self.client = OpenAI()
        
        response = self.client.embeddings.create(
            input=ask,
            model=self.model,
            dimensions=dim if 'text-embedding-3' in self.model else None
        )

        return response.data[0].embedding

    def encode(self, ask, dim=None):
        try:
            return self._encode(ask, dim)
        except Exception as e:
            print(f'Error: {e}')
            time.sleep(2)
            return self.encode(ask, dim)

    def _use_local_backend(self):
        model_name = str(self.model or '').strip().lower()
        if os.getenv('AUTOTQA_FORCE_OPENAI', '').strip().lower() in {'1', 'true', 'yes'}:
            return False
        if model_name.startswith('openai/gpt-oss-20b') or model_name.startswith('gpt-oss-20b'):
            return True
        return os.getenv('DEALOG_LLM_BACKEND', '').strip().lower() == 'local' and bool(os.getenv('LOCAL_LLM_MODEL_PATH'))

    def _query_local(self, ask, post_process=False, get_lower=False):
        if self.local_client is None:
            self.local_client = LLMClient(backend='local', local_model_path=os.getenv('LOCAL_LLM_MODEL_PATH'))
        result = self.local_client.complete(ask, model=self.model, temperature=self.temp if self.temp != -1 else 1, max_tokens=MAX_OUTPUT_LIMIT)
        if not result or not isinstance(result, dict):
            raise RuntimeError('Local LLM call failed')
        ans = str(result.get('content') or '')
        if post_process:
            if get_lower:
                ans = ans.lower().strip().replace('\n', ' ').replace('  ', ' ')
            else:
                ans = ans.strip().replace('\n', ' ').replace('  ', ' ')
        if self.record_log:
            cur_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            self.log[cur_time] = {'ask': ask, 'ans': ans}
            save_json(self.log, os.path.join(self.root_dir, 'log.json'))
        return ans
    
    def query(self, ask, get_lower=False):
        try:
            ans = self._query(ask, get_lower)
            return ans
        except Exception as e:
            print(f'Error: {e}')
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            if 'maximum context length' in str(e):
                raise ValueError(f'E(GPT): Maximum context length exceeded. Please reduce the input length.')
            if 'You exceeded your current quota' in str(e):
                print('!!!!!!!!!!!!!!!! Please change the key file !!!!!!!!!!!!!!!!')
                time.sleep(60*1)
            if 'Content Exists Risk' in str(e):
                raise ValueError(f'E(GPT): Content Exists Risk. Please change the input.')

            return self.query(ask, get_lower)

    def _query(self, ask, post_process=False, get_lower=False):
        if self._use_local_backend():
            return self._query_local(ask, post_process=post_process, get_lower=get_lower)
        key = self.get_key()
        if self.print_key:
            print(f'cur_key: {key}')
        os.environ["OPENAI_API_KEY"] = key
        if self.client is None:
            self.client = OpenAI()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": ask}],
            temperature=self.temp if self.temp != -1 else 1,
            max_tokens=MAX_OUTPUT_LIMIT
        )
        # print(completion)
        ans = completion.choices[0].message.content
        if post_process:
            if get_lower:
                ans = ans.lower().strip().replace('\n', ' ').replace('  ', ' ')
            else:
                ans = ans.strip().replace('\n', ' ').replace('  ', ' ')
        if self.record_log:
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.log[cur_time] = {'ask': ask, 'ans': ans}
            save_json(self.log, os.path.join(self.root_dir, 'log.json'))
        return ans
    

gpt = GPTPOOL(key_file='keys.txt')
