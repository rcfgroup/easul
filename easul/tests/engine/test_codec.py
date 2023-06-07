import numpy as np
from easul.engine.codec import JsonCodec


def test_json_encoder_handles_np_values():
   o = {
            'outcome_step': 'pneumonia_mortality',                                             
            'next_step': 'mortality_low',                                                      
            'reason': 'negative',                                                              
            'context': {                                                                       
               'lime_table_plot': {                                                           
                  'prediction_label': 'Death',                                               
                  'reasons': [                                                               
                     {                                                                      
                        'label': 'Comorb_score',                                           
                        'name': 'Comorb_score',                                            
                        'value': '0.76',                                                   
                        'range': 'greater than 0.47',                                      
                        'effect_size': '-0.16',                                            
                        'positive': False,                                                 
                        'lime_pc': 100                                                     
                     }
                  ]                                                                          
               }                                                                              
            },                                                                                 
            'input_data': {                                                                    
               'ethnicity': float(0.4864864864864865),
               'sex': np.int64(1.0),
               'dbp': float(-0.9899290150319422),
               'temperature': float(-0.8467122208916812),
               'CREA': 0.051369104646312,                                                     
               'K': -1.892464857943289,                                                       
               'GFR': -0.18124323761023986,                                                   
               'Comorb_score': 0.7616122418366646,                                            
               'Spcfc_Comorb': np.int64(1.0),
               'had_Prev_admin': np.int64(0.0)
            },                                                                                 
            'result': {                                                                        
               'value': 1,                                                                    
               'label': 'Death',                                                              
               'probabilities': [                                                             
                  {                                                                          
                     'probability': 0.46,                                                   
                     'label': 'Survival',                                                   
                     'value': 0                                                             
                  },                                                                         
                  {'probability': 0.54, 'label': 'Death', 'value': 1}                        
               ],                                                                             
               'data': {
                  'ethnicity': float(0.4864864864864865),
                  'sex': np.int64(1.0),
                  'dbp': float(-0.9899290150319422),
                  'temperature': float(-0.8467122208916812),
                  'CREA': 0.051369104646312,
                  'K': -1.892464857943289,
                  'GFR': -0.18124323761023986,
                  'Comorb_score': 0.7616122418366646,
                  'Spcfc_Comorb': np.int64(1.0),
                  'had_Prev_admin': np.int64(0.0)
               },
            }                                                                                  
         }
   codec = JsonCodec()
   codec.encode(o)