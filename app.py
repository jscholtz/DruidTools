import streamlit as st
import streamlit.components.v1 as components
import pymongo
import os
import streamlit_antd_components as sac

st.set_page_config(layout="wide")
CRs = ['0','1/4','1/2','1','2','3','4','5','6']
types = ['Beast','Fey']     


@st.cache_resource(show_spinner=False)
def get_client():
    return pymongo.MongoClient(os.environ['mongo_login'])

client = get_client()
collection_basic = client['creatures']['basic_list']
collection_display = client['creatures']['display']

def shrink_text(scale):
    return "body {margin: 0;\ntransform: scale("+str(scale)+");\ntransform-origin: 0 0;}"

if 'selected' not in st.session_state:
    st.session_state['selected'] = False
    st.session_state['just_creatures'] = []
    st.session_state['hit_points'] = []
    st.session_state['max_hit_points'] = []
    st.session_state['creature_displays'] = []
    st.session_state['creature_data'] = []

if 'cr' not in st.session_state:
    st.session_state['cr'] = '1/4' 

def reselect():
    st.session_state['selected'] = False

def cr_change():
    st.session_state['cr'] = st.session_state['input_cr']

def showme():
    st.session_state['creature_selection'] = st.session_state['sac_creature_input']
    st.session_state['selected'] = True
    just_creatures = [k for k in st.session_state['creature_selection'] if k not in CRs]
    just_creatures = [k for k in just_creatures if k not in types]
    st.toast(just_creatures)
    st.session_state['just_creatures'] = st.session_state['just_creatures'] + just_creatures

    hps = []
    maxhps = []
    displays = []
    creatures = []
            
    for item in just_creatures:
        data = list(collection_basic.find({'slug': item}))[0]
        displays.append(list(collection_display.find({'slug': item}))[0])
        creatures.append(data)
        hps.append([data['hit_points']])
        maxhps.append(data['hit_points'])

    st.session_state['hit_points'] = st.session_state['hit_points'] + hps
    st.session_state['max_hit_points'] = st.session_state['max_hit_points'] + maxhps
    st.session_state['creature_displays'] = st.session_state['creature_displays'] + displays
    st.session_state['creature_data'] = st.session_state['creature_data'] + creatures


def pressed_remove(creature_index, bar_index):
    del st.session_state['hit_points'][creature_index][bar_index]
    if st.session_state['hit_points'][creature_index] == []:
        del st.session_state['hit_points'][creature_index]
        del st.session_state['max_hit_points'][creature_index]
        del st.session_state['just_creatures'][creature_index]
        del st.session_state['creature_displays'][creature_index] 
        del st.session_state['creature_data'][creature_index]
    if st.session_state['hit_points'] == []:
        st.session_state['selected'] = False

def pressed_add(creature_index):
    temp = st.session_state['hit_points'][creature_index]
    temp.append(st.session_state['max_hit_points'][creature_index]) 
    st.session_state['hit_points'][creature_index] = temp
    
def change_hitpoints(creature_index, bar_index):
    slider = f"slider_{creature_index:02d}_{bar_index:02d}"
    st.session_state['hit_points'][creature_index][bar_index] = st.session_state[slider]

if not st.session_state['selected']:
    st.header("Creatures")

    menu = []
    
    for ctype in types:
        submenu = []
        for tcr in CRs:
            beasts = list(collection_basic.find({'challenge_rating':tcr, 'type':ctype}))
            entry = sac.CasItem(tcr, children=[sac.CasItem(item['slug']) for item in beasts if item.get('subtype') != 'Swarm'])
            submenu.append(entry)
        entry = sac.CasItem(ctype, children=submenu)
        menu.append(entry)
            
    cols = st.columns([3,6,3])
    with cols[1]:    
        sac.cascader(items=menu, label='Creatures', multiple=True, search=True, clear=True, key='sac_creature_input')
        st.button(label='Show',on_click=showme, type='primary')

if st.session_state['selected']:
    
    #cols = st.columns([1,1,8])
    #with cols[0]:
    st.button('Add more creatures',on_click=reselect, type='primary')

    N = len(st.session_state['just_creatures'])
    if N == 1:
        cols = st.columns([0.5,1,0.5])
        scale=0.9
    elif N == 2:
        cols = st.columns([1,3,0.5,3,1])
        scale=0.7
    elif N == 3:
        cols = st.columns([1,6,0.5,6,0.5,6,1])
        scale=0.6
    elif N == 4:
        cols = st.columns([0.5]+[6,0.5]*N)
        scale=0.5
    elif N > 4:
        cols = st.columns([0.5]+[6,0.5]*N)
        scale=0.4


    for i,item in enumerate(st.session_state['just_creatures']):
        creature_disp = st.session_state['creature_displays'][i]
        creature_data = st.session_state['creature_data'][i]
        bars = st.session_state['hit_points'][i]
        with cols[2*i+1]:
            subcols01 = st.columns([6,1])
            with subcols01[0]:
                st.header(f"{creature_data['name']}")
            with subcols01[1]:
                st.button(label=':heavy_plus_sign:', key=f'btn_add_{i:02d}', on_click=pressed_add,args=(i,))
                
            for j,bar in enumerate(bars):
                subcols = st.columns([6,1])
                with subcols[0]:
                    st.slider('Hitpoints', 0, st.session_state['max_hit_points'][i]+10, bar,
                                label_visibility='collapsed',
                                key=f"slider_{i:02d}_{j:02d}",
                                on_change=change_hitpoints, args=(i,j,))
                with subcols[1]:
                    st.button(label=':x:', key=f'btn_cross_{i:02d}_{j:02d}', on_click=pressed_remove, args=(i,j,))
            text = creature_disp['inline']
            text = text.replace('body { margin: 0;}',shrink_text(scale))
            components.html(text,height=creature_disp['sizes'][0],width=creature_disp['sizes'][1])
