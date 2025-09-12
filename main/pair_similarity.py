import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.utils as ut
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

user_vectors = pd.read_csv('data/processed/user_vectors.csv', index_col=0)

sim_matrix = cosine_similarity(user_vectors.values)
sim_df = pd.DataFrame(sim_matrix, index=user_vectors.index, columns=user_vectors.index)
sim_df.to_csv('data/processed/user_similarity.csv')


HEATMAP = False
PCA_SCATTER = False
GRAFO = False
INTERACTIVE_PCA = False  # Nuevo flag para plotly
INTERACTIVE_HEATMAP = False  # Nuevo flag para heatmap interactivo
INTERACTIVE_GRAFO = True   # Nuevo flag para grafo interactivo

if HEATMAP:
	import seaborn as sns
	import matplotlib.pyplot as plt
	# Selecciona un subconjunto si hay muchos usuarios
	subset = sim_df.iloc[:30, :30]
	plt.figure(figsize=(12, 10))
	sns.heatmap(subset, cmap='viridis')
	plt.title('Heatmap de similitud entre usuarios')
	plt.xlabel('Usuario')
	plt.ylabel('Usuario')
	plt.show()

if INTERACTIVE_HEATMAP:
	import plotly.express as px
	subset = sim_df.iloc[:1042, :1042]
	fig = px.imshow(subset,
					labels=dict(x="Usuario", y="Usuario", color="Similitud"),
					x=subset.columns,
					y=subset.index,
					title="Heatmap de similitud entre usuarios (interactivo)")
	fig.show()

if PCA_SCATTER:
	from sklearn.decomposition import PCA
	import matplotlib.pyplot as plt
	pca = PCA(n_components=2)
	coords = pca.fit_transform(user_vectors.values)
	plt.figure(figsize=(10, 8))
	plt.scatter(coords[:, 0], coords[:, 1], alpha=0.7)
	plt.title('Usuarios proyectados en 2D (PCA)')
	plt.xlabel('PC1')
	plt.ylabel('PC2')
	plt.show()

if INTERACTIVE_PCA:
	from sklearn.decomposition import PCA
	import plotly.express as px
	
	pca = PCA(n_components=2)
	coords = pca.fit_transform(user_vectors.values)
	df_plot = pd.DataFrame(coords, columns=['PC1', 'PC2'])
	df_plot['Usuario'] = user_vectors.index
	fig = px.scatter(df_plot, x='PC1', y='PC2', hover_name='Usuario', title='Usuarios proyectados en 2D (PCA, interactivo)')
	fig.show()

if GRAFO:
	import networkx as nx
	import matplotlib.pyplot as plt
	k = 5
	G = nx.Graph()
	for i, user in enumerate(user_vectors.index):
		G.add_node(user)
		sim_scores = sim_df.loc[user].drop(user)
		top_k = sim_scores.sort_values(ascending=False).head(k)
		for neighbor, score in top_k.items():
			G.add_edge(user, neighbor, weight=score)
	# Dibuja un subgrafo si hay muchos usuarios
	plt.figure(figsize=(12, 12))
	subgraph = G.subgraph(list(user_vectors.index)[:200])
	nx.draw(subgraph, with_labels=True, node_size=300, font_size=8)
	plt.title('Grafo de similitud (k-NN)')
	plt.show()

if INTERACTIVE_GRAFO:
	import networkx as nx
	import plotly.graph_objects as go
	k = 5
	G = nx.Graph()
	for i, user in enumerate(user_vectors.index):
		G.add_node(user)
		sim_scores = sim_df.loc[user].drop(user)
		top_k = sim_scores.sort_values(ascending=False).head(k)
		for neighbor, score in top_k.items():
			G.add_edge(user, neighbor, weight=score)
	# Usa spring layout para posiciones
	pos = nx.spring_layout(G, seed=42)
	# Solo un subgrafo si hay muchos usuarios
	sub_nodes = list(user_vectors.index)[:1042]
	subgraph = G.subgraph(sub_nodes)


	# Permitir al usuario elegir el nodo a resaltar
	print("Usuarios disponibles para resaltar:")
	for idx, usuario in enumerate(sub_nodes):
		print(f"{idx}: {usuario}")
	try:
		idx_usuario = int(input("\nIngresa el número del usuario a resaltar (por defecto 0): ") or 0)
		usuario_destacado = sub_nodes[idx_usuario]
	except (ValueError, IndexError):
		print("Selección inválida, se usará el primero.")
		usuario_destacado = sub_nodes[0]

	# Edges: resalta las conexiones del usuario seleccionado
	edge_x = []
	edge_y = []
	edge_colors = []
	for edge in subgraph.edges():
		x0, y0 = pos[edge[0]]
		x1, y1 = pos[edge[1]]
		edge_x += [x0, x1, None]
		edge_y += [y0, y1, None]
		if usuario_destacado in edge:
			edge_colors.append('red')
		else:
			edge_colors.append('#888')
	edge_trace = go.Scatter(
		x=edge_x, y=edge_y,
		line=dict(width=2, color='red'),
		hoverinfo='none',
		mode='lines')

	# Nodos: resalta el nodo seleccionado
	node_x = []
	node_y = []
	node_text = []
	node_color = []
	for node in subgraph.nodes():
		x, y = pos[node]
		node_x.append(x)
		node_y.append(y)
		node_text.append(str(node))
		if node == usuario_destacado:
			node_color.append('red')
		else:
			node_color.append('blue')
	node_trace = go.Scatter(
		x=node_x, y=node_y,
		mode='markers+text',
		text=node_text,
		hoverinfo='text',
		marker=dict(
			showscale=False,
			color=node_color,
			size=12,
			line_width=2))

	fig = go.Figure(data=[edge_trace, node_trace],
					layout=go.Layout(
						title=f'Grafo de similitud (conexiones de {usuario_destacado} resaltadas)',
						showlegend=False,
						hovermode='closest',
						margin=dict(b=20,l=5,r=5,t=40)))
	fig.show()



