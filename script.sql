SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Products](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[Name] [varchar](500) NULL,
	[CategoryName] [varchar](50) NULL,
	[Price] [numeric](18, 2) NULL,
	[Unit] [varchar](50) NULL,
	[ImageUrl] [varchar](500) NULL,
	[CreatedDate] [datetime] NULL,
	[IsOutofStock] [bit] NULL,
	[OrignialPrice] [numeric](18, 2) NULL,
	[Url] [varchar](500) NULL,
	[Sku] [varchar](50) NULL,
 CONSTRAINT [PK_Products] PRIMARY KEY CLUSTERED 
(
	[Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

