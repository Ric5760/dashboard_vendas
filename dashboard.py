import requests 
import streamlit as st
import pandas as pd 
import plotly.express as px

url = 'https://labdados.com/produtos'
st.set_page_config(layout = 'wide')



st.title('DASHBOARD DE VENDAS :moneybag:')

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''
    
todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023) 
    
query_string = {'regiao':regiao.lower(), 'ano':ano}      

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'


def tabela(url:str,query_string:dict)->pd.DataFrame:
    
    dados = None  # Inicializa dados como None
    
    try:
        response = requests.get(url,params=query_string)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        dados = pd.DataFrame.from_dict(response.json())
        
    except requests.exceptions.RequestException as e:
        st.error(f'Erro ao fazer a requisição para a API: {e}')
     
    except ValueError as e:
        st.error(f'Erro ao converter a resposta da API para JSON: {e}')
        
    except Exception as e:
        st.error(f'Erro inesperado: {e}')
     
    return dados

def criar_receita_mensal(receita_mensal):
    fig_receita_mensal = px.line(receita_mensal,
                                                        x = 'Mes',
                                                        y = 'Preço',
                                                        markers = True,
                                                        range_y = (0, receita_mensal.max()),
                                                        color='Ano',
                                                        line_dash = 'Ano',
                                                        title = 'Receita mensal')

    return fig_receita_mensal.update_layout(yaxis_title = 'Receita')
 
def bar_receita_estados (receita_estados):  
 
    fig_receita_estados = px.bar(receita_estados.head(),
                                            x = 'Local da compra',
                                            y = 'Preço',
                                            text_auto = True,
                                            title = 'Top estados')
    
    return fig_receita_estados.update_layout(yaxis_title = 'Receita')

def bar_receita_categorias (receita_categorias):
    
    fig_receita_categorias = px.bar(receita_categorias,
                                                                text_auto = True,
                                                                title = 'Receita por categoria')
    return fig_receita_categorias.update_layout(yaxis_title = 'Receita')



def criar_mapa_receita(receita_estados):
    """
    Cria um gráfico de mapa da receita por estado.

    Args:
        receita_estados: DataFrame contendo as colunas 'Local da compra', 'lat', 'lon' e 'Preço'.

    Returns:
        Uma figura do Plotly Express contendo o gráfico de mapa.
    """
    fig = px.scatter_geo(receita_estados,
                         lat='lat',
                         lon='lon',
                         scope='south america',
                         size='Preço',
                         template='seaborn',
                         hover_name='Local da compra',
                         hover_data={'lat': False, 'lon': False},
                         title='Receita por Estado')
    return fig


dados = tabela(url,query_string=query_string)

if dados is not None:
    
    filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
    
    if filtro_vendedores:
        dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
        
    receita_estados = dados.groupby('Local da compra')[['Preço']].sum()

    receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
    
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')
    
    receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
    
    receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
    receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
    receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)
    
    aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])
    
    with aba1:
        coluna1, coluna2 = st.columns(2,border=True)
        
        
        with coluna1:
                    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
                    st.plotly_chart(criar_mapa_receita(receita_estados=receita_estados), use_container_width = True)
                    st.plotly_chart(bar_receita_estados (receita_estados=receita_estados), use_container_width = True)
        with coluna2:
                    st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
                    st.plotly_chart(criar_receita_mensal(receita_mensal=receita_mensal), use_container_width = True)
                    st.plotly_chart(bar_receita_categorias (receita_categorias=receita_categorias), use_container_width = True)
    
    with aba2:
        
          coluna1, coluna2 = st.columns(2,border=True)
          
          with coluna1:
                        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
                        
          with coluna2:
                        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
                        
                    
    with aba3:
        
            qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
            ### Tabelas vendedores 
            vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))
            
            fig_receita_vendedores = px.bar(
                                            vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                            x='sum',
                                            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                            text_auto=True,
                                            title=f'Top {qtd_vendedores} vendedores (receita)'
                                        )

            fig_vendas_vendedores = px.bar(
                                vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                x='count',
                                y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                text_auto=True,
                                title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
                            )


            
            coluna1, coluna2 = st.columns(2,border=True)
          
            with coluna1:
                            st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
                            st.plotly_chart(fig_receita_vendedores)
            with coluna2:
                            st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
                            st.plotly_chart(fig_vendas_vendedores)
                  
      
else:
        st.warning('Não foi possível carregar os dados.')