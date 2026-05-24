from .BaseDataset import *

class TQADataset(BaseDataset):
    def __init__(self, dataset_name:str, max_row=-1, max_col=-1):
        super(TQADataset, self).__init__(dataset_name)
        
        self.max_row = max_row
        self.max_col = max_col
        self.tol_data, self.train_data, self.test_data, self.valid_data = [], [], [], []
        self.test_seen_data, self.test_unseen_data = [], []

    def load_data(self, data_path=None):
        if self.dataset_name == 'wiki_qa':
            self.load_wikitq_data(data_path)
        elif self.dataset_name == 'feta_qa':
            self.load_fetaqa_data(data_path)
        elif self.dataset_name == 'fin_qa':
            self.load_finqa_data(data_path)
        elif self.dataset_name == 'bird_qa':
            self.load_birdqa_data(data_path)
        elif self.dataset_name == 'tablebench_nr':
            self.load_tablebench_data(data_path, tgt_qtype='NumericalReasoning')
        elif self.dataset_name == 'tablebench_fc':
            self.load_tablebench_data(data_path, tgt_qtype='FactChecking')
        elif self.dataset_name == 'tablebench':
            self.load_tablebench_data(data_path, tgt_qtype='all')
        else:
            raise ValueError(f"Dataset name {self.dataset_name} is not valid.")

    
    def load_tablebench_data(self, data_path=None, tgt_qtype='NumericalReasoning'):
        if data_path == None:
            data_path = f'{DATA_PATH}/TQA/{self.dataset_name}/'
        print(data_path)
        
        datas = load_jsonl(data_path+'TableBench_DP.jsonl')

        inses = []
        for d in tqdm(datas):
            id = d["id"]
            qtype = d["qtype"]
            if tgt_qtype != 'all' and  qtype != tgt_qtype:
                continue

            qsubtype = d["qsubtype"]
            table = json.loads((d["table"]))
            question = d["question"]
            answer = d["answer"]
            if ', ' in answer:
                answer = answer.replace(', ', '|')
            
            id = f'{id}-{qtype}-{qsubtype}'

            data = {}
            cols = table['columns']
            for col in cols:
                if cols.count(col) > 1:
                    idx = 1
                    for j in range(len(cols)):
                        if cols[j] == col:
                            cols[j] = f'{col}_{idx}'
                            idx += 1

            for col in cols:
                data[col] = []

            for row in table['data']:
                for j in range(len(row)):
                    cell = row[j]
                    data[cols[j]].append(cell)

            # print(data)
            # print(cols)
            # print()

            tbl = pd.DataFrame(data)

            ins = TQAData(dataset_name=self.dataset_name, tbl=tbl, question=question, label=answer, id=id)
            inses.append(ins)

        self.test_data = inses
        self.test_unseen_data = self.test_data
        self.test_seen_data = self.test_data

        self.tol_data = self.train_data + self.valid_data + self.test_data
                    

    def load_birdqa_data(self, data_path=None):
        if data_path == None:
            data_path = f'{DATA_PATH}/TQA/{self.dataset_name}/'
        print(data_path)

        dev = open_json(data_path + 'dev.json')

        inses = []
        for d in tqdm(dev):
            question = d['question']
            answer = d['answer']
            db = d['db']
            difficulty = d['difficulty']
            tbl = d['table']
            title = d['title']
            question_id = d['question_id']

            id = f'{question_id}-{db}-{tbl}-{difficulty}'

            print(tbl)
            df = pd.read_csv(data_path + f'csvs/{tbl}')

            ins = TQAData(dataset_name=self.dataset_name, tbl=df, question=question, label=answer, id=id, title=title)
            inses.append(ins)

        self.test_unseen_data = inses
        self.test_data = self.test_unseen_data

    def load_finqa_data(self, data_path=None):
        if data_path == None:
            data_path = f'{DATA_PATH}/TQA/{self.dataset_name}/'
        print(data_path)

        def tbl_arr_to_df(tbl_arr):
            headers = tbl_arr[0]
            # if headers have duplicates, rename them
            for i in range(len(headers)):
                h = headers[i]
                if headers.count(h) > 1:
                    idx = 1
                    for j in range(len(headers)):
                        if headers[j] == h:
                            headers[j] = f'{h}_{idx}'
                            idx += 1
            
            data = {}
            for i in range(len(headers)):
                data[headers[i]] = []

            for i in range(1, len(tbl_arr)):
                for j in range(len(headers)):
                    data[headers[j]].append(tbl_arr[i][j])
            # print(tbl_arr)
            # print([len(v) for v in tbl_arr])
            # print(data)
            # print()
            tbl = pd.DataFrame(data)
            return tbl
        
        def load_TQAData_from_split(path):
            json_data = open_json(path)
            instances = []
            for d in json_data:
                tbl = d['table']
                qa = d['qa']
                question = qa['question']
                # answer = qa['answer']
                answer = qa['exe_ans']
                gold_inds = qa['gold_inds']

                skip = False
                for evi in gold_inds:
                    if 'table' not in evi:
                        skip = True
                        break
                if skip:
                    continue

                title = 'No title'
                id = d['id']
                df = tbl_arr_to_df(tbl)
                ins = TQAData(dataset_name=self.dataset_name, tbl=df, question=question, label=answer, id=id, title=title)
                instances.append(ins)
            return instances
        
        train = load_TQAData_from_split(data_path + 'train.json')
        valid = load_TQAData_from_split(data_path + 'dev.json')
        test = load_TQAData_from_split(data_path + 'test.json')

        self.train_data = train
        self.valid_data = valid
        self.test_data = test

        self.test_seen_data = valid
        self.test_unseen_data = test

        self.tol_data = self.train_data + self.valid_data + self.test_data

    def load_fetaqa_data(self, data_path=None):
        if data_path == None:
            data_path = f'{DATA_PATH}/TQA/{self.dataset_name}/'
        print(data_path)

        def tbl_arr_to_df(tbl_arr):
            headers = tbl_arr[0]
            count = {}
            for h in headers:
                if h not in count:
                    count[h] = 0
                count[h] += 1
            
            start_from_2_row = False
            # rename the headers
            for i in range(len(headers)):
                h = headers[i]
                if h in count and count[h] > 1:
                    headers[i] = f'{h}_{tbl_arr[1][i]}'
                    start_from_2_row = True

                    # idx = 1  # start from 1
                    # for j in range(len(headers)):
                    #     if headers[j] == h:
                    #         headers[j] = f'{h}_sub_column{idx}'
                    #         idx += 1
            for i in range(len(headers)):
                h = headers[i]
                if headers.count(h) > 1:
                    idx = 1
                    for j in range(len(headers)):
                        if headers[j] == h:
                            headers[j] = f'{h}_{idx}'
                            idx += 1

            assert len(set(headers)) == len(headers), f"Duplicate headers: {headers}"

            data = {}
            for i in range(1 if start_from_2_row else 1, len(tbl_arr)):
                for j in range(len(headers)):
                    if headers[j] not in data:
                        data[headers[j]] = []
                    data[headers[j]].append(tbl_arr[i][j])
            tbl = pd.DataFrame(data)
            return tbl

        def load_TQAData_from_split(path):
            json_data = load_jsonl(path)
            instances = []
            for d in json_data:
                tbl_arr = d['table_array']
                id = d['feta_id']

                page_title = d['table_page_title']
                table_title = d['table_section_title']
                title = f'{table_title} of {page_title}'

                question = d['question']
                answer = d['answer']

                tbl = tbl_arr_to_df(tbl_arr)

                ins = TQAData(dataset_name=self.dataset_name, tbl=tbl, question=question, label=answer, id=id, title=title)
                instances.append(ins)
            return instances
        
        train = load_TQAData_from_split(data_path + f'fetaQA-v1_train.jsonl')
        valid = load_TQAData_from_split(data_path + 'fetaQA-v1_dev.jsonl')
        test = load_TQAData_from_split(data_path + 'fetaQA-v1_test.jsonl')

        self.train_data = train
        self.valid_data = valid
        self.test_data = test

        self.test_seen_data = valid
        self.test_unseen_data = test

        self.tol_data = self.train_data + self.valid_data + self.test_data

    def load_wikitq_data(self, data_path=None):
        
        def load_TQAData_from_split(split:pd.DataFrame, dn:str):

            instances = []

            for i, row in split.iterrows():
                # id,table_id,table,answer
                tbl_path = row['table']
                question = row['question']
                answer = row['answer']
                id = row['id']
                try:
                    tbl=pd.read_csv(os.path.join(data_path, tbl_path), sep=',')
                except:
                    tbl=pd.read_csv(os.path.join(data_path, tbl_path).replace('.csv', '.tsv'), sep='\t')

                # Truncate the table
                if self.max_row > 0:
                    tbl = tbl.head(self.max_row)
                if self.max_col > 0:
                    tbl = tbl.iloc[:, :self.max_col]
                
                # search metadata based on tbl_path
                meta_data_row = meta_data.loc[tbl_path]
                tbl_title = meta_data_row['title']
                tbl_caption = meta_data_row['caption']

                instance = TQAData(dataset_name=dn, tbl=tbl, question=question, label=answer, id=id, title=tbl_title, caption=tbl_caption)
                instances.append(instance)
                
            return instances
            
        if data_path == None:
            data_path = f'{DATA_PATH}/TQA/{self.dataset_name}/'
        print(data_path)
        
        train = pd.read_csv(data_path + 'train.csv')
        test_seen = pd.read_csv(data_path + 'test_seen.csv')
        test_unseen = pd.read_csv(data_path + 'test_unseen.csv')
        meta_data = pd.read_csv(data_path + 'table-metadata.tsv', sep='\t')
        # index column: contextId
        meta_data.set_index('contextId', inplace=True)

        self.train_data = load_TQAData_from_split(train, self.dataset_name)
        self.test_seen_data = load_TQAData_from_split(test_seen, self.dataset_name)
        self.test_unseen_data = load_TQAData_from_split(test_unseen, self.dataset_name)
        self.test_data = self.test_seen_data + self.test_unseen_data
        
        self.tol_data = self.train_data + self.valid_data + self.test_data
