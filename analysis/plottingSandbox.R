# overall Accuracy plot
library(ggplot2)
library(ggthemes)

ggplot(aes(y = centDist, x = glasses, fill=glasses), 
       data = dat) +
  geom_boxplot() +
  labs( 
    x = "Wearable Eye-tracker",
    y = "Visual Angle (deg)",
    title="Accuracy"
    ) +
  scale_fill_brewer(palette="Greens") +
  scale_y_continuous(breaks=seq(0,3,by=1), limits=c(0,3), expand=c(0,.1)) +
  theme(
    aspect.ratio = 1.5,
    panel.background = element_blank(),
    plot.title = element_text(hjust=.5, size=18),
    axis.text = element_text(size = rel(1.4), margin=margin(5)),
    axis.title = element_text(size=rel(1.3)),
    axis.line.y = element_line(colour = "black", 
                             size = .5, linetype = "solid"),
    axis.ticks.x = element_blank(),
    legend.position = "none",
  ) +
  geom_segment(aes(x =.5, y = 0, xend = 3.4, yend = 0), size=.25) + 
  geom_segment(aes(x=.5, y=.5, xend=3.4, yend=.5), size=.75, linetype="twodash", color="darkorange") +
  ggsave("test.pdf", width = 5, height = 8)
