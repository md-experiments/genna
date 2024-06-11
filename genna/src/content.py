
import json
import os
import pandas as pd
from src.utils import hash_text, read_yaml, files_in_dir_any_filter, files_in_dir, add_dict
import yaml

def get_global_vars(inputs_path, config_file_path):
    configs = read_yaml(config_file_path)
    list_configs = list(configs.keys())
    list_configs.sort()
    #dataset_path = f'{data_path}/datasets/'
    list_files = files_in_dir(inputs_path)
    print(list_files)
    list_files = [f.split(os.sep)[-1] for f in list_files if not f.endswith('DS_Store')]
    list_files.sort()
    return list_configs, list_files

class FileManager():
    def __init__(self, path):
        self.path = path
        
    def read_json(self,file):
        if os.path.exists(os.path.join(self.path,file)):
            with open(os.path.join(self.path,file),'r') as f:
                anno_dict = json.load(f)
        else:
            anno_dict = {}
        return anno_dict

    def write_json(self, file, content):
        with open(os.path.join(self.path,file),'w') as f:
            json.dump(content,f)

    def read_csv(self,file):
        if os.path.exists(os.path.join(self.path,file)):
            df = pd.read_csv(os.path.join(self.path,file))
        else:
            df = pd.DataFrame([])
        return df

    def update_json(self, file, entry, reserved_labels):
        anno_dict = self.read_json(file)
        anno_dict, outcome = update_annotation_item(anno_dict, entry, reserved_labels)
        self.write_json(file, anno_dict)
        return outcome

def get_avg_index(idx_prev, idx_next = None):
    """
    Incremental index rows will have the format idx__ind_dec
    0001__0_512 will mean index position 0.512 after position 0001 
    """
    print(idx_prev, idx_next)
    idx_core = idx_prev.split('__')[0]
    if idx_next:
        assert(idx_core==idx_next.split('__')[0])
        idx_prev_loc = '0' if len(idx_prev.split('__'))==1 else idx_prev.split('__')[1]
        idx_prev_loc = float(idx_prev_loc.replace('_','.'))
        idx_next_loc = idx_next.split('__')[1]
        idx_next_loc = float(idx_next_loc.replace('_','.'))
        new_idx = sum([idx_prev_loc,idx_next_loc])/2
        i, d = divmod(new_idx, 1)
        res = f'{idx_core}__{int(i)}_{str(d)[2:10]}'
    else:
        if len(idx_prev.split('__'))==1:
            res = idx_core + '__1'
        else:
            res = idx_core + '__' + str(int(idx_prev.split('__')[1])+1)
            
    return res
    
def config_checks(config, reserved_labels):
    """Makes various checks to config mandatory fields"""
    config_checks_msg = []
    offending_columns = set(config.get('other_columns',[])) & set(config.get('hidden_columns',[])) & set(reserved_labels)
    if len(offending_columns):
        config_checks_msg.append(f"Columns {offending_columns} are reserved and should not be included in config")
    if config.get('video_preview',False):
        if config.get('video_preview_path','')=='':
            config_checks_msg.append(f"Need to specify path for video previews or set previews to false")
    for path in ['video_path','audio_path']:
        if config.get('video_audio_select',False):
            if path not in config.keys():
                config_checks_msg.append(f"Need to specify {path} for content")
            elif not os.path.exists(config[path]):
                config_checks_msg.append(f"{path} does not exist")

    if len(config_checks_msg)==0:
        config_checks_msg = ['Config checks ok']
    return ','.join(config_checks_msg)

def update_annotation_item(anno_dict, entry, reserved_labels):
    """
    Amends the annotation with a new entry. Entry is a dictionary with 'id', 'type', 'value'
    

    returns:
        outcome - whether to increase / decrease counter
    """
    if entry['id'] not in anno_dict.keys():
        anno_dict[entry['id']] = {}

    # Conent is treated different to the rest so will check if update is LABEL, CONTENT or OTHER (currently that means: comment, video, audio)
    reserved_labels_ex_content = reserved_labels.copy()
    reserved_labels_ex_content.remove('content')

    # Updates label values THAT HAVE LABELS ALREADY - a list of labels selected (if a label is unselected -> it will be removed from the list)
    ## NB: label names cannot be 'comment' or 'content'
    if entry['type'] in anno_dict[entry['id']] and entry['type'] not in reserved_labels:  
        if entry['value'] in anno_dict[entry['id']][entry['type']]:
            anno_dict[entry['id']][entry['type']].remove(entry['value'])
            outcome = -1
        else:
            anno_dict[entry['id']][entry['type']].append(entry['value'])
            outcome = 1
    # Updates COMMENT / CONTENT values or LABELS that are new
    else:
        if entry['type'] in reserved_labels_ex_content:
            len_init_value = len(''.join(anno_dict[entry['id']].get(entry['type'],'')))
        elif entry['type'] == 'content':
            # In case of comment value can be edited to empty (ie line can be removed completely where there was text initially)
            if (len(entry['id'].split('__'))==1) and 'content' in anno_dict[entry['id']].keys():
                len_init_value = 1
            elif (len(entry['id'].split('__'))>1) and anno_dict[entry['id']].get('content',[''])[0] != '...':
                len_init_value = 1
            else:
                len_init_value = 0
        # If this is a new row altogether, removing edit means, returning to ...
        if ('remove_edits' in entry.keys()) and (len(entry['id'].split('__'))>1):
            anno_dict[entry['id']]['content'] = ['...']
            len_init_value = 1
            print('hits this')
        # Edits can be created, updated or removed
        elif ('remove_edits' in entry.keys()) and ('content' in anno_dict[entry['id']].keys()):
            del anno_dict[entry['id']]['content']
        else:
            anno_dict[entry['id']][entry['type']] = [entry['value']]

        if entry['type'] not in reserved_labels:
            outcome = 1
        # COMMENT no text now and there was text before (applies only to COMMENT because deleting the whole text is an edit)
        elif len(entry['value'])==0 and len_init_value>0 and entry['type'] in reserved_labels_ex_content:
            outcome = -1
        # CONTENT edit removal on original lines
        elif 'content' not in anno_dict[entry['id']].keys() and len_init_value>0 and entry['type'] == 'content':
            outcome = -1
        # CONTENT edit removal on added lines
        elif (len(entry['id'].split('__'))>1) and anno_dict[entry['id']].get('content',[''])[0] == '...' and len_init_value>0 and entry['type'] == 'content':
            outcome = -1
        # COMMENT there is text now and no text before
        elif len(entry['value'])>0 and len_init_value==0 and entry['type'] in reserved_labels_ex_content:
            outcome = 1
        elif 'content' in anno_dict[entry['id']].keys() and len_init_value==0 and entry['type'] == 'content':
            outcome = 1
        elif (len(entry['id'].split('__'))>1) and anno_dict[entry['id']].get('content',[''])[0] != '...' and len_init_value==0 and entry['type'] == 'content':
            outcome = 1
        # COMMENT and there was text before and there is text now OR there was no text and there is still no text
        else:
            outcome = 0
    return anno_dict, outcome

class DataSet():
    def __init__(self, file, input_path, annotations_path, config_name, config_file_path):
        self.reserved_labels = ['comment','content','media_audio_anno','media_video_anno']
        self._read_config(config_name, config_file_path)
        self.cm_d = FileManager(input_path)
        self.cm_a = FileManager(annotations_path)
        self.file = file
        self.df_items = self.cm_d.read_csv(self.file)
        self.file_path_annotations =f"{self.file.replace('.csv','').replace('.txt','')}_{config_name}_annotations.txt"
        self.annotations = self.cm_a.read_json(self.file_path_annotations)

        # Tracks line entries added to the annotation doc
        self.added_lines_dict = self._get_added_lines_obj()

    def _read_config(self,config_name, config_file_path):
        read_configs = read_yaml(config_file_path)
        config = read_configs[config_name]

        button_colors = ['primary','secondary','success','warning','info','light']
        self.labels = [
            {'name':lbl.lower(),'title':lbl,'button_style':button_colors[i], 'count': 0} for i,lbl in enumerate(config['labels_config'])
        ]
        self.labels_list = [lbl['name'] for lbl in self.labels]
        self.nr_comments = 0
        self.nr_edits = 0
        self.editor_features = dict(
            allow_comments = config.get('allow_comments',False),
            content_editable = config.get('content_editable',False),
            video_audio_select = config.get('video_audio_select',False),
            add_lines = config.get('add_lines',False),
            video_preview = config.get('video_preview',False),
        )
        # Required if video preview is True
        self.video_preview_path = config.get('video_preview_path','')
        self.video_preview_url_column = config.get('video_preview_url_column','')
        self.other_columns = config.get('other_columns',[])
        self.hidden_columns = config.get('hidden_columns',[])
        self.config_checks_msg = config_checks(config, self.reserved_labels)
        print(self.config_checks_msg)
        self.audio_files = files_in_dir_any_filter(config.get('audio_path',''), ['.mp3'], full_path = False)
        self.video_files =  files_in_dir_any_filter(config.get('video_path',''), ['.mp4','.mpeg','.jpeg','.jpg'], full_path = False)
        self.index_col = config['index_cols']
        self.target = config['target']

    def _get_annotated_content(self,hash_idx,field_name,place_holder_text = ''):
        text_out = '; '.join(self.annotations.get(hash_idx,{}).get(field_name,[]))
        if text_out == '':
            text_out = place_holder_text
        return text_out

    def _get_added_lines_obj(self):
        added_lines_dict = {}
        for a in self.annotations:
            if len(a.split('__'))>1:
                if a.split('__')[0] in added_lines_dict:
                    added_lines_dict[a.split('__')[0]].append(a)
                else:
                    added_lines_dict[a.split('__')[0]] = [a]
        return added_lines_dict

    def _read_dataset_item(self, ii, idx, t, dict_other, force_hash = None):
        if force_hash:
            hash_idx = force_hash
        else:
            hash_idx = hash_text(idx)
        content_annotated_text = self._get_annotated_content(hash_idx,'content')
        content_value = t if len(content_annotated_text)==0 else content_annotated_text
        if (len(content_annotated_text)>0) and (len(hash_idx.split('__'))==1):
            content_edited = True
        elif (len(hash_idx.split('__'))>1) and content_annotated_text != '...':
            content_edited = True
        else:
            content_edited = False
        d = {
            'nr': ii,
            'id': idx,
            'content':content_value,
            'content_edited': content_edited,
            'labels': self.annotations.get(hash_idx,{}).get('labels',[]), 
            'comment': self._get_annotated_content(hash_idx,'comment'),
            'hash_id': hash_idx,
            'media_audio_anno': self._get_annotated_content(hash_idx,'media_audio_anno','...'),
            'media_video_anno': self._get_annotated_content(hash_idx,'media_video_anno','...'),
        }
        d = add_dict(d,dict_other)
        return d, hash_idx

    def _update_counts(self,d):
        for lbl in self.labels:
            lbl['count'] = lbl.get('count',0) + (1 if lbl['name'] in d['labels'] else 0)
        self.nr_comments = self.nr_comments + (1 if len(d['comment']) else 0)
        self.nr_edits = self.nr_edits + (1 if d['content_edited'] else 0)

    def all(self):
        """Retrieve all items and prepare them to be shown on the page.
        Return data: list object which will be read out on the page
        """
        reserved_labels_in_use = any([c in self.labels_list for c in self.reserved_labels])
        # Lists all points
        if len(self.df_items) == 0:
            data = [{
                    'nr': 0,
                    'id': 0,
                    'content': f'NA: No data yet',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x',
                    'video_preview_url': ''
                    }]
        elif (self.index_col in self.df_items.columns) and (self.target in self.df_items.columns) and (not reserved_labels_in_use):
            data = []
            self.d_idx = []
            #for lbl in self.labels:
            #    lbl['count'] = 0
            overall_idx = 0
            for ii, idx in enumerate(self.df_items[self.index_col]):
                t = self.df_items[self.target].iloc[ii]
                dict_other = {}
                for col in self.other_columns:
                    dict_other[col] = self.df_items[col].iloc[ii]
                for col in self.hidden_columns:
                    dict_other[col] = self.df_items[col].iloc[ii]
                if self.editor_features['video_preview']:
                    if isinstance(self.df_items[self.video_preview_url_column].iloc[ii], str):
                        if self.video_preview_path.startswith('https://'):
                            dict_other['video_preview_url'] = f'{self.video_preview_path}{self.df_items[self.video_preview_url_column].iloc[ii]}'
                        else:
                            dict_other['video_preview_url'] = os.path.join(self.video_preview_path,self.df_items[self.video_preview_url_column].iloc[ii])
                    else:
                        dict_other['video_preview_url'] = ''
                d, hash_idx = self._read_dataset_item(overall_idx, idx, t, dict_other)
                self._update_counts(d)
                data.append(d)
                self.d_idx.append(hash_idx)
                
                overall_idx = overall_idx+1
                if hash_idx in self.added_lines_dict:
                    list_added_lines = self.added_lines_dict[hash_idx]
                    list_added_lines.sort()
                    for _, hash_anno_idx in enumerate(list_added_lines):

                        t = self.get_target(hash_anno_idx)
                        dict_other = {col:'' for col in self.other_columns}
                        dict_other = {col:'' for col in self.hidden_columns}
                        d, hash_idx = self._read_dataset_item(overall_idx, 'new', t, dict_other, hash_anno_idx)
                        self._update_counts(d)
                        data.append(d)    
                        self.d_idx.append(hash_idx)
                        overall_idx = overall_idx+1
        elif reserved_labels_in_use:
            data = [{
                    'nr': 0,
                    'id': 0,
                    'content': f'NA: Config not allowed, cannot have labels with names: {", ".join(self.reserved_labels)}',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x',
                    'video_preview_url': ''
                    }]
        else:
            data = [{
                    'nr': 0,
                    'id': 0,
                    'content':'NA: Data not compatible with this config',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x',
                    'video_preview_url': ''
                    }]
        self.ds_list = data
        
    def get_target(self, hash_idx):
        """Retrieve target content from original doc by hash_idx
        The raw doc still has its original index in column index_col
        We have a hash_idx to look for here so we need to loop through all items, hash them and check for match
        """
        if len(hash_idx.split('__'))>1:
            # Check if this is an item added by the creative
            target = ';'.join(self.annotations[hash_idx].get('content',['...']))
        else:
            for ii, idx in enumerate(self.df_items[self.index_col]):
                if hash_idx == hash_text(idx):
                    target = self.df_items[self.target].iloc[ii]
                    break
        return target

    def add_line(self, input_idx, content = '...'):
        core_idx = input_idx.split('__')[0]
        matched_core_idx_ls = [a for a in self.annotations if f'{core_idx}__' in a]
        matched_core_idx_ls.sort()
        # Assert input_idx is either same as core or in the added ones
        assert(any([core_idx == input_idx, input_idx in matched_core_idx_ls]))
        # Finding the next key: input_idx is the line we will add below. 
        # For input_idx there are two options: it is part of the original list (i.e. input_idx == core_idx) or it was added by the creative
        # In the latter case, it will be in the matched_core_idx_ls and we need to find the item after it, after sorting
        if core_idx == input_idx and len(matched_core_idx_ls)==0:
            # input_idx is in the original AND there are no added items to it yet
            next_idx = None
        elif core_idx == input_idx and len(matched_core_idx_ls)>0:
            next_idx = matched_core_idx_ls[0]
        else:
            position_in_matched = matched_core_idx_ls.index(input_idx)
            if position_in_matched+1 == len(matched_core_idx_ls):
                # This index is the last of the added ones
                next_idx = None
            else:
                next_idx = matched_core_idx_ls[position_in_matched+1]

        idx = get_avg_index(input_idx, idx_next = next_idx)
        
        entry = {'id': str(idx), 'value':content, 'type':'content'}
        print(entry)
        outcome = self.cm_a.update_json(self.file_path_annotations, entry, self.reserved_labels)
        self.annotations = self.cm_a.read_json(self.file_path_annotations)
        if core_idx in self.added_lines_dict:
            self.added_lines_dict[core_idx].append(idx)
        else:
            self.added_lines_dict[core_idx] = [idx]
        return outcome

    def annotate(self, idx, content, label_type, remove_edits=False):
        # adds to annotations file: comment, content edits and labels
        entry = {'id': str(idx), 'value':content, 'type':label_type}
        if remove_edits:
            entry['remove_edits'] = True
            if len(idx.split('__'))>1:
                self.added_lines_dict[idx.split('__')[0]].remove(idx)
                if len(self.added_lines_dict[idx.split('__')[0]])==0:
                    del self.added_lines_dict[idx.split('__')[0]]
        outcome = self.cm_a.update_json(self.file_path_annotations, entry, self.reserved_labels)
        self.annotations = self.cm_a.read_json(self.file_path_annotations)
        return outcome

